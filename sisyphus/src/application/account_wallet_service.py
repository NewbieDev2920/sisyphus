from domain.ports.account_port import AccountPort

class AccountWalletService:
    def __init__(self, account : AccountPort):
        self.account = account

    def get_summary(self) -> str:
        return self.account.summary()
