from domain.events.event import Event

class PriceUpdate(Event):
    def __init__(self,price : float, symbol : str):
        self.price = price
        self.symbol = symbol