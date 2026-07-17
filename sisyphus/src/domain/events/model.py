from domain.events.event import Event
from typing import Any, List

class TrainingUpdate(Event):
    """
    Evento emitido cuando un modelo de Machine Learning finaliza su entrenamiento.
    Transporta el modelo empaquetado (pipeline) listo para hacer predicciones.
    """
    def __init__(self, model_name: str, fitted_pipeline: Any, target: str, features: List[str], 
                 target_meaning: str = "", regressors_meaning: dict = None, 
                 regressors_transformations: dict = None, weights: dict = None):
        self.model_name = model_name
        self.fitted_pipeline = fitted_pipeline
        self.target = target
        self.features = features
        self.target_meaning = target_meaning
        self.regressors_meaning = regressors_meaning or {}
        self.regressors_transformations = regressors_transformations or {}
        self.weights = weights or {}
