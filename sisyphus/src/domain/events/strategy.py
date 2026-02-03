from domain.signals import Signal
from domain.events.event import Event

class StatCalculated(Event):
    def __init__(self, name : str, value : float, index):
        self.name = name
        self.value = value
        self.index = index

class SignalEvent(Event):
    def __init__(self, signal : Signal, numeric_value):
        self.signal = signal
        self.numeric_value = numeric_value