from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.events.model import TrainingUpdate
from collections import deque
import pandas as pd
import numpy as np

class EGARCHPredictor(Base):
    """
    Ejecutor (Predictor) para el modelo EGARCH.
    Escucha pasivamente por eventos `TrainingUpdate` para cargar un modelo `arch` ajustado (ARCHModelResult).
    Ante cada actualización, añade el nuevo retorno a una ventana rodante y 
    produce un forecast analítico t+1 de varianza condicional.
    """

    def __init__(self, symbol: str, fsm, expected_target: str, window_size: int = 100):
        self.symbol = symbol
        self.fsm = fsm
        self.name = self.__class__.__name__
        self.expected_target = expected_target
        
        self.model_result = None
        self.current_variance = 0.0
        
        # EGARCH necesita el historial reciente de residuos para proyectar
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.is_ready = False
        
        self.target_meaning = ""
        self.model_weights = {}

    def update(self, event: Event):
        if isinstance(event, TrainingUpdate):
            if event.target == self.expected_target:
                print(f"[{self.name}] Recibido nuevo modelo EGARCH para {self.expected_target}.")
                self.model_result = event.fitted_pipeline
                self.target_meaning = event.target_meaning
                self.model_weights = event.weights
                self.is_ready = True

        elif isinstance(event, PriceUpdate):
            # En producción, PriceUpdate o Feeder insertaría el retorno aquí
            # Para propósitos de este Predictor, guardaremos el valor crudo en la ventana rodante
            self.history.append(float(event.price) * 100) # Escalar por 100 como en el Trainer
            self._predict()

    def _predict(self):
        if not self.is_ready or self.model_result is None or len(self.history) < 5:
            return

        try:
            # En arch, podemos proveer nuevos datos a un resultado existente (si construimos el modelo sobre ellos)
            # Pero para hacerlo fácil de manera rodante, la forma recomendada en arch >= 4.0:
            # model.forecast(y=new_y, horizon=1)
            
            y_recent = pd.Series(list(self.history))
            
            # Reutilizamos el modelo base que viene en model_result
            base_model = self.model_result.model
            
            # Calculamos varianzas condicionales para la ventana usando los parámetros entrenados
            # forecast() simula o calcula analíticamente la varianza de horizon pasos adelante
            # Pasando los parámetros pre-calculados a un nuevo array (y_recent)
            forecasts = base_model.forecast(params=self.model_result.params, y=y_recent, horizon=1)
            
            # El último elemento del pronóstico de 1 paso adelante
            var_t1 = forecasts.variance.iloc[-1, 0]
            
            # Desescalamos la varianza (dividimos entre 10000 porque el precio se multiplicó por 100)
            self.current_variance = float(var_t1) / 10000.0
            
        except Exception as e:
            print(f"Error durante predicción EGARCH: {e}")

    def get_forecast(self) -> float:
        """
        Retorna la varianza condicional esperada en t+1.
        """
        return self.current_variance

    def configuration_map(self) -> str:
        status = "READY" if self.is_ready else "WAITING FOR MODEL"
        
        weights_str = "\\n        ".join([f"{k}: {v:.6f}" for k, v in self.model_weights.items()]) if self.model_weights else "None"
        
        config = f"""-------
        PREDICTOR: {self.name}
        -------
        SYMBOL: {self.symbol}
        STATUS: {status}
        PREDICTOR (y_hat): {self.expected_target} -> {self.target_meaning}
        CURRENT VAR (t+1): {self.current_variance:.8f}
        
        MODEL WEIGHTS (Coefficients):
        {weights_str}
        """
        return config
