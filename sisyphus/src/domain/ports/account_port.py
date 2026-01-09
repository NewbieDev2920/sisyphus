from abc import abstractmethod
from abc import ABC

class AccountPort(ABC):

    #WALLET INFO---------------

    #property
    @abstractmethod
    def equity():
        pass

    #property
    @abstractmethod
    def cash():
        pass

    #property
    @abstractmethod
    def pending_transfer():
        #Must be pending out and pending in funds.
        pass

    #MARKET VALUE---------------

    #property
    @abstractmethod
    def long_market_value():
        pass

    #DISPLAY--------------------

    @abstractmethod
    def summary():
        pass


    



    



