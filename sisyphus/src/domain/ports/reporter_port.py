from abc  import ABC, abstractmethod
from domain.events.event import Event

class ReporterPort:

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def update(self, event : Event):
        pass

    @abstractmethod
    def journal(self) -> list:
        pass