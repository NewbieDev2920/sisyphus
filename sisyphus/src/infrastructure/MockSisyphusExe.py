from domain.ports.fsm import SisyphusExePort
from domain.events.execution import *

class MockSisyphusExe(SisyphusExePort):

    def __init__(self):

    def buy(self, symbol, notional):
        print(f"BUYED {symbol} : NOTIONAL {notional}")
        event = OrderSent("something here")

    def sell(self, symbol, notional):
        print(f"SELLED {symbol} : NOTIONAL {notional}")
        event = OrderSent("something here")

    def buy(self, symbol, qty):
        print(f"BUYED {symbol} : QTY {qty}")
        event = OrderSent("something here")

    def sell(self, symbol, qty):
        print(f"SELLED {symbol}: QTY {qty}")
        event = OrderSent("something here")