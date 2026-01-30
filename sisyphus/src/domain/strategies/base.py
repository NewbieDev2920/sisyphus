from abc import ABC, abstractmethod
from domain.events.event import Event
from domain.signals import Signal

class Base(ABC):

    def __init__(self, symbol : str):
        self.symbol = symbol

    @abstractmethod
    def update(self, event : Event):
        pass

    @abstractmethod
    def compute_signal(self, signal : Signal):
        pass