from computations.ewma import next_ewma_point_alpha

class EWMALogReturnForecaster:
    """
    Suavizador/Pronosticador de Log-Retornos usando EWMA.
    
    Siguiendo la Opción 4: Clase explícita e independiente. No hereda de Base.
    Recibe log-retornos crudos (ruidosos) y los suaviza delegando a `computations`.
    """

    def __init__(self, symbol: str, alpha: float, data_type: str = "Log Returns", interval: str = "1m"):
        self.symbol = symbol
        self.data_type = data_type
        self.interval = interval
        self.name = self.__class__.__name__
        self.alpha = alpha
        
        self.smoothed_return = 0.0
        self.is_initialized = False

    def update(self, log_return: float) -> float:
        """
        Actualiza y devuelve el log retorno suavizado.
        """
        if not self.is_initialized:
            self.smoothed_return = log_return
            self.is_initialized = True
        else:
            # Reutilizamos la capa matemática pura
            self.smoothed_return = next_ewma_point_alpha(self.smoothed_return, log_return, self.alpha)
            
        return self.smoothed_return

    def get_forecast(self) -> float:
        return self.smoothed_return

    def configuration_map(self) -> str:
        config = f"""-------
        FORECASTER: {self.name}
        -------
        SYMBOL: {self.symbol}
        DATA TYPE: {self.data_type}
        TIME INTERVAL: {self.interval}
        ALPHA: {self.alpha}
        CURRENT SMOOTHED RETURN: {self.smoothed_return}
        """
        return config
