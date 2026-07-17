from domain.events.event import Event

class DiscordNotification(Event):

    def __init__(self, message: str):
        self.message = message