from datetime import datetime
import datetime
class PriceRecord:
    
    def __init__(self, date : datetime, symbol : str, value : float, purgeable: bool):
        """
        Symbol may be SISYPHUS_PORTFOLIO
        """
        self.date : datetime = str(date)
        self.symbol: str = symbol
        self.value : float = value
        self.purgeable : bool = purgeable