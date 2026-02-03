from domain.strategies.base import Base
from domain.events.event import Event
from domain.signals import Signal
from domain.events.strategy import SignalEvent

class Manual(Base):

    def __init__(self, symbol : str, fsm):
        self.symbol = symbol
        self.fsm = fsm
        self.name = self.__class__.__name__

    def update(self, event : Event):
        print("No update needed for manual strategy.")

    def compute_signal(self, signal : Signal, numeric_value):
        self.fsm.on_event(SignalEvent(signal, numeric_value))

    def buy(self, qty : float):
        self.compute_signal(Signal.BUY, qty)

    def sell(self, qty : float):
        self.compute_signal(Signal.SELL, qty)

    def buy_notional(self, notional : float):
        self.compute_signal(Signal.BUY_NOTIONAL, notional)

    def sell_notional(self, notional : float):
        self.compute_signal(Signal.SELL_NOTIONAL, notional)