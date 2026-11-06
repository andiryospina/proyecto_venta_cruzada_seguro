"""Líneas base del torneo: lo que cualquier modelo serio debe vencer.

La línea base "no llamar a nadie" sale de `DummyClassifier`. La regla de negocio vive aquí porque es la referencia que más
importa: es lo que el equipo comercial haría **sin** un modelo.
"""
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin


class DamageRuleClassifier(BaseEstimator, ClassifierMixin):
    """Regla simple: "llamar si el vehículo tuvo daño".

    Aprende del entrenamiento una sola cosa: la tasa de aceptación de los clientes con daño y de los que no lo tienen.
    Con esas dos tasas entrega probabilidades, de modo que se puede evaluar con las mismas métricas que un modelo
    (PR-AUC, log loss, costo). Recibe el DataFrame **limpio** (etapa 3), con `Vehicle_Damage` en 0/1.
    """

    def __init__(self, column: str = "Vehicle_Damage"):
        self.column = column

    def fit(self, X, y):
        values = np.asarray(X[self.column])
        y = np.asarray(y)
        self.classes_ = np.array([0, 1])
        self.rates_ = {int(v): float(y[values == v].mean()) for v in np.unique(values)}
        self.global_rate_ = float(y.mean())
        return self

    def predict_proba(self, X):
        positive = np.array([self.rates_.get(int(v), self.global_rate_) for v in np.asarray(X[self.column])])
        return np.column_stack([1 - positive, positive])

    def predict(self, X):
        return (np.asarray(X[self.column]) == 1).astype(int)
