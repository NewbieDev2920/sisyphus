
from datetime import datetime
class BotLog:
    
    def __init__(self, date : datetime, postman : str, value : str, purgeable: bool, log_type: int):
        """
        String parse a datetime object.
        Postman is the class/object type who reports the log.
        value can be a JSON String Object in case of ORDER or TRADE Log Type.
        """
        self.date : datetime = str(date)
        self.postman  = postman
        self.value = value
        self.purgeable = purgeable
        self.log_type = log_type
