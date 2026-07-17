from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.events.model import TrainingUpdate
import pandas as pd
import numpy as np

class LinearRegressionPredictor(Base):
    """
    Ejecutor (Predictor) para el modelo de Regresión Lineal.
    Esta clase NO entrena modelos. Escucha pasivamente por eventos `TrainingUpdate`
    para cargar en memoria un Pipeline pre-entrenado. Luego, ante cada actualización
    de datos de mercado, ejecuta una predicción.
    
    Esta predicción (`get_forecast()`) se expone como un Factor para ser consumida
    por modelos superiores como XGBOOST o Random Forest.

    Transformaciones Personalizadas Soportadas:
    El Pipeline que esta clase recibe aplica transformaciones matemáticas automáticamente 
    gracias a FunctionTransformer en Sklearn. Soporta polinomios (x**d), np.log, 
    np.exp y funciones trigonométricas (np.sin, np.cos).
    """

    def __init__(self, symbol: str, fsm, expected_target: str, expected_features: list):
        """
        :param expected_target: Validar que el modelo recibido predice esto.
        :param expected_features: Validar que el modelo recibido usa estos factores.
        """
        self.symbol = symbol
        self.fsm = fsm
        self.name = self.__class__.__name__
        self.expected_target = expected_target
        self.expected_features = expected_features
        
        self.model_pipeline = None
        self.current_prediction = 0.0
        
        # Guardar las variables en tiempo real necesarias para la predicción
        self.live_features = {feature: 0.0 for feature in self.expected_features}
        self.is_ready = False
        
        # Metadata Semántica y Pesos del Modelo
        self.target_meaning = ""
        self.regressors_meaning = {}
        self.regressors_transformations = {}
        self.model_weights = {}

    def update(self, event: Event):
        # 1. Escuchar actualización del modelo
        if isinstance(event, TrainingUpdate):
            if event.target == self.expected_target:
                print(f"[{self.name}] Recibido nuevo modelo entrenado para {self.expected_target}. Actualizando Pipeline...")
                self.model_pipeline = event.fitted_pipeline
                self.target_meaning = event.target_meaning
                self.regressors_meaning = event.regressors_meaning
                self.regressors_transformations = event.regressors_transformations
                self.model_weights = event.weights
                self.is_ready = True

        # 2. Escuchar actualización de mercado
        elif isinstance(event, PriceUpdate):
            # Simulamos que actualizamos los factores X en tiempo real
            # (En producción, escucharíamos eventos provenientes de los Feeders o calculados localmente)
            self.live_features['x1'] = float(event.price) * 0.9 # Simulación
            self.live_features['x2'] = float(event.price) * 1.1 # Simulación
            
            # Ejecutar inferencia
            self._predict()

    def _predict(self):
        """
        Inyecta las variables en vivo al pipeline y guarda la predicción.
        """
        if not self.is_ready or self.model_pipeline is None:
            return

        try:
            # Ensamblar DataFrame de 1 fila para inferencia
            df_live = pd.DataFrame([self.live_features])
            
            # El pipeline de sklearn automáticamente aplica los logaritmos, senos y potencias configurados en el Trainer.
            prediction_array = self.model_pipeline.predict(df_live)
            
            self.current_prediction = float(prediction_array[0])
            
        except Exception as e:
            print(f"Error durante predicción de regresión lineal: {e}")

    def get_forecast(self) -> float:
        """
        Expone el factor predictivo a un modelo superior.
        """
        return self.current_prediction

    def configuration_map(self) -> str:
        status = "READY" if self.is_ready else "WAITING FOR MODEL"
        
        meanings = "\\n        ".join([f"{k}: {v} (Transform: {self.regressors_transformations.get(k, 'Linear')})" for k, v in self.regressors_meaning.items()]) if self.regressors_meaning else "None"
        weights_str = "\\n        ".join([f"{k}: {v:.6f}" if isinstance(v, float) else f"{k}: {v}" for k, v in self.model_weights.items()]) if self.model_weights else "None"
        
        config = f"""-------
        PREDICTOR: {self.name}
        -------
        SYMBOL: {self.symbol}
        STATUS: {status}
        PREDICTOR (y_hat): {self.expected_target} -> {self.target_meaning}
        CURRENT PRED (y_hat): {self.current_prediction}
        
        REGRESSORS MEANING (X):
        {meanings}
        
        MODEL WEIGHTS (Coefficients):
        {weights_str}
        """
        return config
