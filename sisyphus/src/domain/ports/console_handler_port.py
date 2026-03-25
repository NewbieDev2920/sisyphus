from abc import ABC, abstractmethod

class ConsoleHandlerPort(ABC):

    def __init__(self, toggle_bot = True):
        self.toggle_bot = toggle_bot

    @abstractmethod
    def print_bot(self):
        pass

    @abstractmethod
    def print_stream(self):
        pass

    @abstractmethod
    def toggle(self):
        pass

