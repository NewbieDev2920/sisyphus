from domain.strategies.base import Base
from computations.rolling_avg import next_sma_point
from domain.events.discord_notification import DiscordNotification
from domain.events.strategy import SignalEvent
from domain.events.market import PriceUpdate
from domain.signals import Signal
from infrastructure.console_handler import get_console_handler
from datetime import datetime
from collections import deque
from domain.events.event import Event

class SimpleMovingAverages(Base):

    def __init__(self, symbol: str, fsm, short_tail: int, long_tail: int, data_type: str = "Raw Prices", interval: str = "1m"):
        self.symbol = symbol
        self.fsm = fsm
        self.data_type = data_type
        self.interval = interval
        self.name = self.__class__.__name__
        self.qty = 0
        self.l = long_tail
        self.s = short_tail
        self.sma_l = 0
        self.sma_s = 0
        self.trend = None
        self.window = deque([0]*self.l, maxlen=self.l)
        self.asset_price : float = 0


    def update(self, event : Event):
        
        if isinstance(event, PriceUpdate):
            #Cambiar precio crudo por log(retorno)
            self.sma_crossover(event.price)

    def compute_signal(self, signal : Signal, numeric_value):
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
        LONG_TAIL_LENGTH (Window size):{self.l}\n
        SHORT_TAIL_LENGTH (Window size):{self.s}\n
        LONG TAIL MOVING AVERAGE: {self.sma_l}\n
        SHORT TAIL MOVING AVERAGE: {self.sma_s}\n
        TREND {"BULL" if self.trend else "BEAR"}
        """
        return config

    def sma_crossover(self, value: float):
        # O(1) Delegation to computational layer
        # Calculate new values using purely functional mathematics
        # The oldest element in the short window is at index `self.l - self.s` because the window size is `self.l`
        old_val_s = self.window[len(self.window) - self.s] if len(self.window) >= self.s else 0
        self.sma_s = next_sma_point(self.sma_s, value, old_val_s, self.s)
        
        old_val_l = self.window[0] if len(self.window) == self.l else 0
        self.sma_l = next_sma_point(self.sma_l, value, old_val_l, self.l)
        
        self.window.append(value)

        if self.trend == None:
            if self.sma_s-self.sma_l > 0:
                self.trend = True
            else:
                self.trend = False
        else:
            if self.sma_s - self.sma_l > 0 and not self.trend:
                self. trend = True
                notify_event = DiscordNotification(f"{self.symbol} is on a bull trend: {str(datetime.now())}.")
                self.fsm.on_event(notify_event)
            if self.sma_s - self.sma_l < 0 and self.trend:
                self.trend = False
                notify_event = DiscordNotification(f"{self.symbol} is on a bear trend: {str(datetime.now())}")
                self.fsm.on_event(notify_event)



