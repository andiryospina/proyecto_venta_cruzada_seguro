"""Pipeline completo (variables + modelo) y modelos de referencia con parámetros fijos.

El pipeline se guarda **entero**: la app de Streamlit carga un solo objeto que recibe las columnas limpias y devuelve
probabilidades, sin repetir ningún cálculo a mano.
"""
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from proyecto.features.engineering import FeatureOptions, build_preprocessor

RANDOM_STATE = 42


def reference_models(random_state: int = RANDOM_STATE) -> dict:
    """Dos modelos de parámetros fijos para comparar variables (no para ganar un torneo).

    - `lightgbm`: árboles; capturan solos interacciones y curvas, así que miden lo que las variables aportan **de verdad**.
    - `regresion_logistica`: lineal; necesita que las relaciones se le entreguen ya "dibujadas" (tramos, marcas), así que
      es donde las variables nuevas más pueden ayudar. Requiere `FeatureOptions(scale=True)`.
    """
    return {
        "lightgbm": LGBMClassifier(n_estimators=200, learning_rate=0.08, num_leaves=31, min_child_samples=100,
                                   subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                                   random_state=random_state, n_jobs=4, verbose=-1),
        "regresion_logistica": LogisticRegression(max_iter=500, C=1.0, random_state=random_state),
    }


def build_pipeline(model, options: FeatureOptions = FeatureOptions()) -> Pipeline:
    """Variables que aprenden del entrenamiento + modelo, en un solo objeto."""
    return Pipeline([("features", build_preprocessor(options)), ("model", model)])
