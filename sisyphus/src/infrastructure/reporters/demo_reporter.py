from domain.ports.reporter_port import ReporterPort
from domain.events.event import Event
from domain.events.market import PriceUpdate

class DemoReporter(ReporterPort):

    def __init__(self):
        self.relevant_events = []
        self.journal_entries = []

    def update(self, event :Event):
        if type(event) is PriceUpdate:
            self.relevant_events.append(Event)
            self.journal_entries.append(f"{event.symbol} : {event.price}")

    def journal(self) -> list:
        return self.journal_entries