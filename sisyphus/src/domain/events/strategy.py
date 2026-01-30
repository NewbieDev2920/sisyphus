from domain.signals import Signal

class StatCalculated(Event):
    def __init__(self, name : str, value : float, index):
        self.name = name
        self.value = value
        self.index = index

class SignalEmitted(Event):
    def __init__(self, signal : Signal, index):
        self.signal = signal
        self.index = index