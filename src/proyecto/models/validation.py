"""Validación final del modelo con el conjunto de prueba (specs/005-validacion).

Reglas que este módulo hace cumplir:
- la prueba se abre UNA sola vez (`open_test_once` deja una marca y se niega a abrirla de nuevo);
- la calibración se decide con la regla escrita antes de mirar (`should_calibrate`), usando solo datos de entrenamiento;
- cada cliente aparece una sola vez, así que remuestrear filas es remuestrear clientes.
Lo que se calcula después de abrir la prueba (segmentos, sensibilidad) es solo para reportar: no cambia el modelo.
"""
import getpass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold

from proyecto.config import AGE_BANDS, COST_MATRIX, SEED, SENSITIVITY_RATIOS
from proyecto.models.train import build_pipeline, expected_cost, split_xy
from proyecto.models.tuning import make_lgbm

CALIBRATION_FOLDS = 3
OTHERS_LABEL = "otras"


def _row_log_loss(y_true, proba) -> np.ndarray:
    """Log loss de cada cliente (su promedio es el log loss de sklearn)."""
    y_true = np.asarray(y_true, dtype=int)
    proba = np.clip(np.asarray(proba, dtype=float), 1e-6, 1 - 1e-6)
    return -(y_true * np.log(proba) + (1 - y_true) * np.log(1 - proba))


def bootstrap_log_loss_difference(y_true, proba_a, proba_b, n_boot: int = 1000,
                                  seed: int = SEED) -> tuple[float, float, float]:
    """Diferencia de log loss (A menos B) con intervalo del 95 %, remuestreando clientes. Negativo: A tiene mejores probabilidades."""
    diff = _row_log_loss(y_true, proba_a) - _row_log_loss(y_true, proba_b)
    return bootstrap_mean(diff, n_boot=n_boot, seed=seed)


def should_calibrate(raw: dict, calibrated: dict, log_loss_diff: tuple[float, float, float]) -> bool:
    """Regla de la spec (medida en la reserva, nunca en la prueba). Se calibra solo si se cumplen las dos condiciones:

    1. mejora mínima del log loss: TODO el intervalo del 95 % de (calibrado − sin calibrar) está bajo cero, es decir, la
       mejora se distingue del ruido (mismo criterio que la regla de la etapa 06);
    2. el costo de negocio no sube.
    `log_loss_diff` es la salida de `bootstrap_log_loss_difference(y, proba_calibrada, proba_sin_calibrar)`.
    """
    _, _, high = log_loss_diff
    return high < 0 and calibrated["cost"] <= raw["cost"]


def fit_final_model(train: pd.DataFrame, params: dict, calibrate: bool, seed: int = SEED):
    """Modelo final: LightGBM con las mismas variables del torneo, ajustado con TODO el entrenamiento que se le pase.

    Si `calibrate` es True, el pipeline completo se envuelve en una calibración isotónica con 3 pliegues estratificados
    (cada pliegue calibra con clientes que su modelo no vio).
    """
    X, y = split_xy(train)
    pipeline = build_pipeline(make_lgbm(params, random_state=seed), use_engineered=True)
    if not calibrate:
        return pipeline.fit(X, y)
    folds = StratifiedKFold(CALIBRATION_FOLDS, shuffle=True, random_state=seed)
    return CalibratedClassifierCV(pipeline, method="isotonic", cv=folds).fit(X, y)


def open_test_once(marker_path: str | Path, test_path: str | Path, decisions: dict, commit: str) -> pd.DataFrame:
    """Abre la prueba una sola vez y deja constancia en `marker_path`.

    Se niega (sin leer el archivo) si la marca ya existe o si alguna decisión congelada está vacía.
    """
    marker_path = Path(marker_path)
    if marker_path.exists():
        raise FileExistsError(
            f"La prueba ya se abrió (ver {marker_path.name}). No se abre otra vez: si algo no gusta, se anota como límite."
        )
    empty = [name for name, value in decisions.items() if value is None or value == ""]
    if empty:
        raise ValueError(f"Faltan decisiones congeladas antes de abrir la prueba: {', '.join(empty)}")
    data = pd.read_parquet(test_path)
    marker_path.write_text(
        "Prueba abierta una sola vez (specs/005-validacion)\n"
        f"fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"usuario: {getpass.getuser()}\n"
        f"commit: {commit}\n"
        f"archivo: {Path(test_path).name} ({len(data)} filas)\n",
        encoding="utf-8",
    )
    return data


def bootstrap_mean(values, n_boot: int = 1000, seed: int = SEED) -> tuple[float, float, float]:
    """Promedio con intervalo del 95 %, remuestreando clientes. Devuelve (promedio, límite inferior, límite superior)."""
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    boot = values[rng.integers(0, len(values), size=(n_boot, len(values)))].mean(axis=1)
    return float(values.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def age_band(age) -> pd.Series:
    """Tramo de edad de cada cliente según `AGE_BANDS` (cada tramo incluye su edad mínima)."""
    labels = [label for label, _ in AGE_BANDS]
    edges = [start for _, start in AGE_BANDS] + [np.inf]
    return pd.cut(pd.Series(age), bins=edges, labels=labels, right=False).astype(str)


def segment_table(segments, y_true, decision, min_size: int | None = None, cost=COST_MATRIX) -> pd.DataFrame:
    """Por segmento: clientes, costo por cliente, % contactado, % real de interesados y recall.

    Los segmentos con menos de `min_size` clientes se agrupan como "otras" (para no mostrar grupos muy pequeños).
    """
    table = pd.DataFrame({
        "segment": pd.Series(segments).astype(str).to_numpy(),
        "y": np.asarray(y_true, dtype=int),
        "decision": np.asarray(decision, dtype=int),
    })
    if min_size is not None:
        sizes = table["segment"].map(table["segment"].value_counts())
        table.loc[sizes < min_size, "segment"] = OTHERS_LABEL
    cost = np.asarray(cost, dtype=float)
    table["cost"] = cost[table["y"], table["decision"]]
    table["hit"] = table["y"] * table["decision"]
    grouped = table.groupby("segment")
    result = pd.DataFrame({
        "clients": grouped.size(),
        "cost": grouped["cost"].mean(),
        "contact_rate": grouped["decision"].mean(),
        "positive_rate": grouped["y"].mean(),
        "recall": grouped["hit"].sum() / grouped["y"].sum().replace(0, np.nan),
    })
    return result.reset_index().sort_values("clients", ascending=False, ignore_index=True)


def cost_sensitivity(y_true, decision, ratios=SENSITIVITY_RATIOS) -> dict:
    """Costo por cliente con la MISMA decisión y matrices [[0, 1], [r, 0]]: ¿qué pasa si perder un interesado cuesta r llamadas?"""
    return {r: expected_cost(y_true, decision, cost=[[0, 1], [r, 0]]) for r in ratios}
