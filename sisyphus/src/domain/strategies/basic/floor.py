from domain.strategies.base import Base
from domain.events.event import Event
from domain.events.discord_notification import DiscordNotification
from domain.events.strategy import SignalEvent
from domain.events.market import PriceUpdate
from domain.signals import Signal
from infrastructure.console_handler import get_console_handler
from datetime import datetime

#stop-loss strategy
class Floor(Base):
    def __init__(self,symbol : str, fsm ,floor_price : float = 1.0):
        self.fsm = fsm
        self.name = __class__.__name__
        self.symbol : str = symbol
        self.floor_price : float = floor_price
        self.qty = 0
        self.asset_price : float = 0
    
    def update(self, event: Event):
        if isinstance(event, PriceUpdate):
            # Obtener el QTY actualizado directamente desde la cuenta conectada al FSM
            self.qty = self.fsm.asset_qty()
            self.floor(event)
            self.asset_price = event.price

    def configuration_map(self) -> str:
        config = f"""-------
        STRATEGY: {self.name} \U0001f6ab
        -------
        SYMBOL : {self.symbol}\n
        ASSET PRICE : {self.asset_price}\n
        QTY: {self.qty}
        FLOOR PRICE: {self.floor_price}\n
        DIFFERENCE : {self.asset_price - self.floor_price} {"\u26A0\uFE0F" if self.asset_price - self.floor_price < 0 else "\u2705"}
        """
        return config

    def notify(self):
        message = f" \u26A0\uFE0F FLOOR STOP-LOSS ACTIVATED | {self.symbol} | {str(datetime.now())}"
        get_console_handler().print_bot(message)
        self.fsm.on_event(DiscordNotification(message))
        

    def compute_signal(self, signal : Signal, numeric_value):
        self.fsm.on_event(SignalEvent(signal, numeric_value))

    def floor(self, price_update : PriceUpdate):

        if price_update.price - self.floor_price <= 0 and self.qty > 0:
            self.compute_signal(Signal.SELL, self.qty) #Sell all positions
            self.notify()
            
