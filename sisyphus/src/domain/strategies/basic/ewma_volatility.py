from computations.ewma import next_ewma_point_alpha

class EWMAVolatilityForecaster:
    """
    Pronosticador de volatilidad basado en el modelo EWMA (RiskMetrics).
    Acepta log-retornos y calcula la varianza móvil ponderada exponencialmente.
    
    Siguiendo la Opción 4: Esta clase es totalmente independiente, no hereda de Base 
    y no se acopla a la FSM ni emite órdenes. Delega la matemática a `computations`.
    """

    def __init__(self, symbol: str, lambda_decay: float = 0.94, data_type: str = "Log Returns", interval: str = "1d"):
        self.symbol = symbol
        self.data_type = data_type
        self.interval = interval
        self.name = self.__class__.__name__
        
        # En RiskMetrics, lambda suele ser 0.94 para datos diarios
        self.lambda_decay = lambda_decay 
        # El 'alpha' de ewma es (1 - lambda)
        self.alpha = 1 - lambda_decay
        
        self.variance = 0.0
        self.volatility = 0.0
        self.is_initialized = False

    def update(self, log_return: float) -> float:
        """
        Actualiza el pronóstico de volatilidad usando un nuevo log retorno.
        Retorna la volatilidad estimada actual.
        """
        # El input matemático para RiskMetrics es el retorno al cuadrado
        squared_return = log_return ** 2
        
        if not self.is_initialized:
            self.variance = squared_return
            self.is_initialized = True
        else:
            # Reutilizamos la capa matemática de computations para mantener O(1)
            self.variance = next_ewma_point_alpha(self.variance, squared_return, self.alpha)
            
        self.volatility = self.variance ** 0.5
        return self.volatility
        
    def get_forecast(self) -> float:
        return self.volatility

    def configuration_map(self) -> str:
        config = f"""-------
        FORECASTER: {self.name}
        -------
        SYMBOL: {self.symbol}
        DATA TYPE: {self.data_type}
        TIME INTERVAL: {self.interval}
        LAMBDA DECAY: {self.lambda_decay}
        CURRENT VOLATILITY: {self.volatility}
        CURRENT VARIANCE: {self.variance}
        """
        return config
