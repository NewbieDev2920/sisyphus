from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.signals import Signal
import pandas as pd

class MonotonicIncreasing(Base):
    def __init__(self, symbol : str, interval_size = 7):
        self.symbol = symbol
        self.average_slope = -3
        self.interval_prices = []
        self.interval_size = interval_size
        #BORRAR, NO COMETER PECADO CAPITAL.
        self.realtimemarketdata = None
        self.output = []

    def update(self, event : Event):
        if type(event) is PriceUpdate:
            if len(self.interval_prices) >= self.interval_size:
                self.monotonic_increasing()
            else:
                self.interval_prices.append(event.price)

    def compute_signal(self, signal : Signal):
        self.output.append(f"OUTPUT SIGNAL : {str(signal)}")

    def monotonic_increasing(self):
        interval_slopes = []
        for i in range(self.interval_size-1):
            interval_slopes.append(self.interval_prices[i+1]-self.interval_prices[i])
        mu = pd.Series(interval_slopes).mean()
        if mu <= self.average_slope:
            self.compute_signal(Signal.SELL)
        else:
            self.compute_signal(Signal.HOLD)
        self.interval_prices = []
        self.average_slope = mu







