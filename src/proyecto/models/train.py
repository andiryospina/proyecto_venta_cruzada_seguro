"""Pipeline completo (variables + modelo) y modelos de referencia con parámetros fijos.

El pipeline se guarda **entero**: la app de Streamlit carga un solo objeto que recibe las columnas limpias y devuelve
probabilidades, sin repetir ningún cálculo a mano.
"""
from lightgbm import LGBMClassifier
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from proyecto.features.engineering import FeatureOptions, build_preprocessor
from proyecto.models.baselines import DamageRuleClassifier

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


# Variables decididas en el notebook 04 (`reports/04_features.md`): se quitan Vintage, Driving_License y Gender.
TOURNAMENT_FEATURES = FeatureOptions(drop=("Vintage", "Driving_License", "Gender"))                 # variante A (modelos de árboles)
TOURNAMENT_FEATURES_LINEAR = TOURNAMENT_FEATURES.with_changes(age_splines=True, scale=True)         # variante C (regresión: edad como curva)


def tournament_candidates(random_state: int = RANDOM_STATE) -> dict:
    """Candidatos del torneo, todos con **parámetros fijos** (sin ajustar: eso es la etapa 6) y las mismas variables.

    Dos líneas base ("no llamar a nadie" y la regla "llamar si hubo daño") y cinco modelos: uno simple (regresión), uno
    interpretable (árbol), un bosque y dos de boosting.
    """
    trees = TOURNAMENT_FEATURES
    return {
        "línea base: no llamar a nadie": DummyClassifier(strategy="prior"),
        "línea base: llamar si hubo daño": DamageRuleClassifier(),
        "regresión logística": build_pipeline(LogisticRegression(max_iter=500, C=1.0, random_state=random_state), TOURNAMENT_FEATURES_LINEAR),
        "árbol de decisión": build_pipeline(DecisionTreeClassifier(max_depth=5, min_samples_leaf=200, random_state=random_state), trees),
        "bosque aleatorio": build_pipeline(RandomForestClassifier(n_estimators=150, max_depth=16, min_samples_leaf=50, max_features="sqrt",
                                                                  n_jobs=4, random_state=random_state), trees),
        "LightGBM": build_pipeline(reference_models(random_state)["lightgbm"], trees),
        "XGBoost": build_pipeline(XGBClassifier(n_estimators=200, learning_rate=0.08, max_depth=6, subsample=0.8, colsample_bytree=0.8,
                                                tree_method="hist", n_jobs=4, eval_metric="logloss", random_state=random_state), trees),
    }
