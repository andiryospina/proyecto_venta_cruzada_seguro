"""Tarjetas, tabla de sensibilidad y tabla de segmentos a partir de `07_metricas_test.json` y `07_segmentos.csv`.

Principio VII: todo número sale del archivo; si falta una clave, la tarjeta no se arma (no se rellena con ceros).
"""
from dataclasses import dataclass

import pandas as pd

VARIABLE_LABELS = {"Gender": "Género", "Age": "Edad", "Region_Code": "Región"}
SEGMENT_COLUMNS = ["variable", "segment", "clients", "cost", "contact_rate", "positive_rate", "gap_contact_vs_real", "recall"]


@dataclass(frozen=True)
class MetricCard:
    """Una tarjeta de la pestaña de resultados: título, valor ya formateado y una ayuda corta."""
    label: str
    value: str
    help: str = ""


def format_number(value: float, decimals: int = 4) -> str:
    """Número con coma decimal y punto de miles (`0,3312`, `76.222`)."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\0").replace(".", ",").replace("\0", ".")


def format_percent(value: float, decimals: int = 1) -> str:
    """Fracción como porcentaje español (`0.365` → `36,5 %`)."""
    return f"{format_number(value * 100, decimals)} %"


def _get(data, *keys):
    """Valor anidado o `None` si algún nivel falta (o no es un diccionario)."""
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return None
        data = data[key]
    return data


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _interval(values, decimals: int = 4) -> str:
    low, high = values
    return f"IC 95 %: [{format_number(low, decimals)}; {format_number(high, decimals)}]"


def build_metric_cards(metrics: dict | None) -> list[MetricCard]:
    """Tarjetas del bloque `prueba` del JSON. Solo incluye las que se pueden armar con lo que trae el archivo."""
    model = _get(metrics, "prueba", "modelo")
    cards: list[MetricCard] = []

    def add(label, value, formatter, help_text=""):
        if _is_number(value):
            cards.append(MetricCard(label, formatter(value), help_text))

    def interval_of(values):
        ok = isinstance(values, (list, tuple)) and len(values) == 2 and all(_is_number(v) for v in values)
        return _interval(values) if ok else ""

    cost_help = "Menor es mejor. " + interval_of(_get(model, "cost_ic95"))
    add("Costo por cliente", _get(model, "cost"), lambda v: format_number(v, 4), cost_help.strip())
    add("Costo de la regla de negocio", _get(metrics, "prueba", "linea_base", "cost"), lambda v: format_number(v, 4),
        str(_get(metrics, "decisiones", "linea_base") or "Línea base del negocio."))
    add("Diferencia frente a la regla de negocio", _get(metrics, "prueba", "diferencia_costo", "valor"),
        lambda v: format_number(v, 4), ("Modelo menos regla; bajo cero es mejor. " + interval_of(_get(metrics, "prueba", "diferencia_costo", "ic95"))).strip())
    add("% de la base a llamar", _get(model, "contact_rate"), format_percent, "Parte de los clientes que supera el umbral de decisión.")
    add("Recall", _get(model, "recall"), format_percent, "De los interesados, cuántos se llaman.")
    add("Precisión", _get(model, "precision"), format_percent, "De los llamados, cuántos se interesan.")
    add("PR-AUC", _get(model, "pr_auc"), lambda v: format_number(v, 3), "Métrica técnica principal.")
    add("ROC-AUC", _get(model, "roc_auc"), lambda v: format_number(v, 3))
    add("Interesados al llamar al 20 %", _get(model, "capture_20"), format_percent, "Parte de los interesados que quedan en el 20 % mejor puntuado.")
    return cards


def sensitivity_rows(metrics: dict | None) -> list[dict]:
    """Costo del modelo y de la regla según R (cuánto cuesta no llamar a un comprador), ordenado por R."""
    table = _get(metrics, "prueba", "sensibilidad")
    if not isinstance(table, dict):
        return []
    rows = []
    for key, values in table.items():
        head = str(key).split("_")[0]
        model_cost, base_cost = _get(values, "modelo"), _get(values, "linea_base")
        if not (head.isdigit() and _is_number(model_cost) and _is_number(base_cost)):
            continue
        rows.append({
            "_r": int(head),
            "R": f"R = {head}",
            "Costo del modelo": format_number(model_cost, 4),
            "Costo de la regla": format_number(base_cost, 4),
            "Mejor": "Modelo" if model_cost < base_cost else "Regla de negocio",
        })
    rows.sort(key=lambda row: row["_r"])
    return [{k: v for k, v in row.items() if k != "_r"} for row in rows]


def segments_by_variable(df: pd.DataFrame | None) -> dict[str, pd.DataFrame]:
    """Una tabla legible por variable (género, edad, región...) a partir de `07_segmentos.csv`; `{}` si no sirve."""
    if df is None or not set(SEGMENT_COLUMNS) <= set(df.columns):
        return {}
    tables = {}
    for variable, group in df.groupby("variable", sort=False):
        tables[VARIABLE_LABELS.get(str(variable), str(variable))] = pd.DataFrame({
            "Segmento": group["segment"].astype(str).to_list(),
            "Clientes": [format_number(v, 0) for v in group["clients"]],
            "Costo por cliente": [format_number(v, 4) for v in group["cost"]],
            "% que se llama": [format_percent(v) for v in group["contact_rate"]],
            "% real de interesados": [format_percent(v) for v in group["positive_rate"]],
            "Brecha (llama − real)": [format_percent(v) for v in group["gap_contact_vs_real"]],
            "Recall": [format_percent(v) for v in group["recall"]],
        })
    return tables


def hero_stats(metrics: dict | None) -> list[tuple[str, str]]:
    """Tres cifras de la portada de la app: (valor ya formateado, etiqueta). Lo que falta en el JSON no se muestra."""
    stats: list[tuple[str, str]] = []
    contact = _get(metrics, "prueba", "modelo", "contact_rate")
    recall = _get(metrics, "prueba", "modelo", "recall")
    cost = _get(metrics, "prueba", "modelo", "cost")
    rule = _get(metrics, "prueba", "linea_base", "cost")
    if _is_number(contact):
        stats.append((format_percent(contact), "de la lista a llamar"))
    if _is_number(recall):
        stats.append((format_percent(recall), "de los interesados encontrados"))
    if _is_number(cost) and _is_number(rule) and rule > 0 and cost < rule:
        stats.append((f"−{format_percent((rule - cost) / rule, 0)}", "de costo frente a la mejor regla"))
    return stats


def decision_threshold(cost_matrix) -> float | None:
    """Probabilidad desde la que conviene llamar, según la matriz [[0, llamada inútil], [venta perdida, 0]]: c01 / (c01 + c10)."""
    try:
        wasted_call, lost_sale = float(cost_matrix[0][1]), float(cost_matrix[1][0])
    except (TypeError, ValueError, IndexError, KeyError):
        return None
    total = wasted_call + lost_sale
    return wasted_call / total if wasted_call > 0 and lost_sale > 0 else None
