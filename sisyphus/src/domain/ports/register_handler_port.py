from abc import ABC, abstractmethod

class RegisterHandlerPort(ABC):

    @abstractmethod
    def register_symbol(self):
        pass

    @abstractmethod
    def unregister_symbol(self):
        pass

    @abstractmethod
    def registration_list(self):
        pass