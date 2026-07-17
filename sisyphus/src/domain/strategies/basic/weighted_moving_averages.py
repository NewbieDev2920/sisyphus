from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.discord_notification import DiscordNotification
from domain.events.strategy import SignalEvent
from domain.events.market import PriceUpdate
from domain.signals import Signal
from infrastructure.console_handler import get_console_handler
from datetime import datetime
from collections import deque
from computations.rolling_avg import compute_wma
import numpy as np

class WeightedMovingAverages(Base):

    def __init__(self, symbol: str, fsm, long_tail : int, short_tail : int, weights_l : list, weights_s : list, data_type: str = "Raw Prices", interval: str = "1m"):
        self.symbol = symbol
        self.data_type = data_type
        self.interval = interval
        self.qty = 0
        self.fsm = fsm
        self.name = self.__class__.__name__
        self.l = long_tail
        self.s = short_tail
        try:
            if len(weights_l) != self.l or len(weights_s) != self.s:
                raise Exception("Weights vector length must match window length.")
            self.weight_l = np.array(weights_l)
            self.weight_s = np.array(weights_s)
            self.weight_l_sum = np.dot(self.weights_l,np.array([1]*self.l))
            self.weight_s_sum = np.dot(self.weight_s, np.array([1]*self.s))
        except Exception as e:
            print(e)
        self.wma_l = 0
        self.wma_s = 0

        # Por el momento es una métrica exhaustiva(A nivel de modelo) que contempla BULL y BEAR. Sin embargo, es imperante que contemple FLAT.
        self.trend = None

        self.window_l = deque([0]*self.l, maxlen=self.l)
        self.window_s = deque([0]*self.s, maxlen=self.s)
        self.asset_price: float = 0   


    def update(self, event : Event):
        
        if isinstance(event, PriceUpdate):
            #cambiar precio crudo por log(retorno)
            self.wma_crossover(event.price)


    def compute_signal(self):
        pass

    def configuration_map(self) -> str:
        config = f"""-------
        STRATEGY : {self.name}
        -------
        SYMBOL : {self.symbol}
        DATA TYPE: {self.data_type}
        TIME INTERVAL: {self.interval}
        QTY: {self.qty}
        ASSET PRICE : {self.asset_price}
        LONG TAIL LENGTH : {self.l}
        SHORT TAIL LENGTH : {self.s}
        LONG TAIL WEIGHT : {self.weight_l}
        SHORT TAIL WEIGHT : {self.weight_s}
        LONG TAIL MOVING AVERAGE: {self.wma_l}\n
        SHORT TAIL MOVING AVERAGE: {self.wma_s}\n
        TREND {"BULL" if self.trend else "BEAR"}
        """
        return config

    def wma_crossover(self, value : float):
        # O(n) Delegación computacional
        self.window_l.append(value)
        self.window_s.append(value)

        # Usar padding con ceros si las ventanas no están llenas aún para evitar error de dimensiones
        list_l = list(self.window_l) if len(self.window_l) == self.l else [0]*(self.l - len(self.window_l)) + list(self.window_l)
        list_s = list(self.window_s) if len(self.window_s) == self.s else [0]*(self.s - len(self.window_s)) + list(self.window_s)

        self.wma_l = compute_wma(list_l, self.weight_l)
        self.wma_s = compute_wma(list_s, self.weight_s)

        if self.trend == None:
            if self.wma_s-self.sma_l > 0:
                self.trend = True
            else:
                self.trend = False
        else:
            if self.wma_s - self.wma_l > 0 and not self.trend:
                self. trend = True
                notify_event = DiscordNotification(f"{self.symbol} is on a bull trend: {str(datetime.now())}.")
                self.fsm.on_event(notify_event)
            if self.wma_s - self.wma_l < 0 and self.trend:
                self.trend = False
                notify_event = DiscordNotification(f"{self.symbol} is on a bear trend: {str(datetime.now())}")
                self.fsm.on_event(notify_event)
        
