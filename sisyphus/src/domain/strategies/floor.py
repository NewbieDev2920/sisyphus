from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.signals import Signal
import pandas as pd
from infrastructure.console_handler import get_console_handler

class Floor(Base):
    def __init__(self,symbol : str):
        self.symbol : str = symbol
    
    def update():
        pass

    def compute_signal(self, signal : Signal, numeric_value):
        pass

    def floor(price_update : PriceUpdate):
        pass