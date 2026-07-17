from domain.ports.reporter_port import ReporterPort
from domain.events.event import Event
from domain.events.discord_notification import DiscordNotification 
from domain.events.market import PriceUpdate
from domain.events.fsm import OrderResolved
from infrastructure.console_handler import get_console_handler
import requests

class DiscordReporter(ReporterPort):
    
    def __init__(self,destiny_channel):
        self.destiny_channel = destiny_channel

    def update(self, event : Event):

        if isinstance(event, DiscordNotification):
            self.send_to_discord(event.message)
    
    def send_to_discord(self, message : str):
        if not self.destiny_channel:
            get_console_handler().print_bot(f"(!) There is no destiny channel assigned, the next notification will not reach discord. {message}")
            return 

        data = {"content":message, "username": "Sisyphus"}

        try:
            response = requests.post(self.destiny_channel, json = data, timeout = 5)
            response.raise_for_status()
        except Exception as e:
            get_console_handler().print_bot(f"Failed to send Discord webhook post for FSM notification")
        


        
