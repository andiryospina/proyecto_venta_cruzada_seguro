"""Transformadores propios que aprenden de entrenamiento (van dentro del Pipeline)."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_is_fitted

from proyecto.config import PREMIUM_CAP_QUANTILE


class PremiumTransformer(BaseEstimator, TransformerMixin):
    """Recorta la prima anual por arriba al percentil aprendido en entrenamiento y luego aplica log1p.

    Decisión de negocio (2026-10-31): la cola alta de la prima es real (esos clientes se interesan más),
    así que NO se borran filas; solo se limita su peso. El tope (`cap_`) se calcula en `fit`, es decir,
    solo con los datos de entrenamiento.
    """

    def __init__(self, quantile: float = PREMIUM_CAP_QUANTILE):
        self.quantile = quantile

    def fit(self, X, y=None):
        X = check_array(X, dtype=float)
        self.cap_ = float(np.quantile(X, self.quantile))
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self, X):
        check_is_fitted(self, "cap_")
        X = check_array(X, dtype=float)
        return np.log1p(np.minimum(X, self.cap_))

    def get_feature_names_out(self, input_features=None):
        return np.asarray(input_features if input_features is not None else ["Annual_Premium"], dtype=object)
