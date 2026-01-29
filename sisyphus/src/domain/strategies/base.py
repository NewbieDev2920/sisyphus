from abc import ABC, abstractmethod


def Base(ABC):

    def __init__(self, symbol : str):
        self.symbol = symbol

    @abstractmethod
    def update(self, event):
        pass