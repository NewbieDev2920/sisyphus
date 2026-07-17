from domain.strategies.base import Base
from computations.ewma import next_ewma_point_alpha
from domain.events.discord_notification import DiscordNotification
from domain.events.strategy import SignalEvent
from domain.events.market import PriceUpdate
from domain.signals import Signal
from datetime import datetime
from domain.events.event import Event

class ExponentialMovingAverages(Base):

    def __init__(self, symbol: str, fsm, short_alpha: float, long_alpha: float, data_type: str = "Raw Prices", interval: str = "1m"):
        self.symbol = symbol
        self.fsm = fsm
        self.data_type = data_type
        self.interval = interval
        self.name = self.__class__.__name__
        self.qty = 0
        
        # Parámetros alfa para corto y largo plazo (rango de 0 a 1)
        self.alpha_s = short_alpha
        self.alpha_l = long_alpha
        
        self.ewma_l = 0.0
        self.ewma_s = 0.0
        self.trend = None
        self.asset_price: float = 0.0
        self.is_initialized = False

    def update(self, event: Event):
        if isinstance(event, PriceUpdate):
            self.asset_price = float(event.price)
            self.qty = self.fsm.asset_qty()
            # Delegación a nuestra capa computacional funcional
            self.ewma_crossover(self.asset_price)

    def compute_signal(self, signal: Signal, numeric_value):
        pass
        
    def notify(self, message:str):
        pass

    def configuration_map(self) -> str:
        config = f"""-------
        STRATEGY: {self.name}
        -------
        SYMBOL: {self.symbol}
        DATA TYPE: {self.data_type}
        TIME INTERVAL: {self.interval}
        QTY: {self.qty}
        ASSET PRICE : {self.asset_price}
        SHORT ALPHA : {self.alpha_s}
        LONG ALPHA : {self.alpha_l}
        LONG EWMA: {self.ewma_l}
        SHORT EWMA: {self.ewma_s}
        TREND {"BULL" if self.trend else "BEAR"}
        """
        return config

    def ewma_crossover(self, value: float):
        # O(1) Inicialización
        if not self.is_initialized:
            # Sembramos el EWMA con el primer precio para evitar un sesgo inicial hacia cero
            self.ewma_s = value
            self.ewma_l = value
            self.is_initialized = True
            return

        # O(1) Delegación a la capa computacional (Paradigma Funcional Pura)
        self.ewma_s = next_ewma_point_alpha(self.ewma_s, value, self.alpha_s)
        self.ewma_l = next_ewma_point_alpha(self.ewma_l, value, self.alpha_l)

        # Lógica de Trading (Decisión de tendencia)
        if self.trend is None:
            if self.ewma_s - self.ewma_l > 0:
                self.trend = True
            else:
                self.trend = False
        else:
            if self.ewma_s - self.ewma_l > 0 and not self.trend:
                self.trend = True
                notify_event = DiscordNotification(f"{self.symbol} is on a bull trend: {str(datetime.now())}.")
                self.fsm.on_event(notify_event)
                
            if self.ewma_s - self.ewma_l < 0 and self.trend:
                self.trend = False
                notify_event = DiscordNotification(f"{self.symbol} is on a bear trend: {str(datetime.now())}")
                self.fsm.on_event(notify_event)
