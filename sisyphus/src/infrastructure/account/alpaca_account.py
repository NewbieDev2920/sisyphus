from alpaca.trading.client import TradingClient
from domain.ports.account_port import AccountPort

class AlpacaAccount(AccountPort):
    
    def __init__(self, trading_client : TradingClient):
        self.trading_client = trading_client
        self.account = trading_client.get_account()

    #UTILITIES

    #Updates data.
    def refresh(self):
        self.account = self.trading_client.get_account()

    #ACCOUNT INFO

    @property
    def id(self):
        self.refresh()
        return self.account.id

    @property
    def account_number(self):
        self.refresh()
        return self.account.account_number

    @property
    def status(self):
        self.refresh()
        return self.account.status

    #WALLET INFO---------------

    @property
    def equity(self):
        self.refresh()
        return self.account.equity

    @property
    def cash(self):
        self.refresh()
        return self.account.cash

    @property
    def pending_transfer(self):
        self.refresh()
        return {"pending_transfer_in": self.account.pending_transfer_in, "pending_transfer_out" : self.account.pending_transfer_out}

    #MARKET VALUE---------------
    @property
    def long_market_value(self):
        self.refresh()
        return self.account.long_market_value

    #Display
    def summary(self) -> str:
        self.refresh()
        return f"""
        ALPACA ACCOUNT

        WALLET

        #BALANCE
        [x]| cash : {self.account.cash}
        [x]| equity : {self.account.equity}
        [x]| pending_transfer_in : {self.account.pending_transfer_in}
        [x]| pending_transfer_out : {self.account.pending_transfer_out}

        #BALANCE CHANGE
        [x]| balance_change : {float(self.account.equity) - float(self.account.last_equity)}
        [x]| balance_change_percentage : {((float(self.account.equity) - float(self.account.last_equity)) / float(self.account.last_equity)) * 100} %

        # MARKET
        [x]| long_market_value : {self.account.long_market_value}

        #Alpaca Profile
        [x]| account_number : {self.account.account_number}
        [x]| status : {self.account.status}
        """