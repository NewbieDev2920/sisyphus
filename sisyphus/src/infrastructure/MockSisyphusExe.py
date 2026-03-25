from domain.ports.executor_port import ExecutorPort
from infrastructure.console_handler import get_console_handler
from domain.events.execution import *

class MockSisyphusExe(ExecutorPort):

    def __init__(self):
        pass # Added pass to make __init__ syntactically correct

    def buy(self, symbol, notional):
        get_console_handler().print_bot(f"BUYED {symbol} : NOTIONAL {notional}")
        event = OrderSent("something here")

    def sell(self, symbol, notional):
        get_console_handler().print_bot(f"SELLED {symbol} : NOTIONAL {notional}")
        event = OrderSent("something here")

    def buy(self, symbol, qty):
        get_console_handler().print_bot(f"BUYED {symbol} : QTY {qty}")
        event = OrderSent("something here")

    def sell(self, symbol, qty):
        get_console_handler().print_bot(f"SELLED {symbol}: QTY {qty}")
        event = OrderSent("something here")