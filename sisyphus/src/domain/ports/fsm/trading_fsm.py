from domain.ports.fsm.states import State
from domain.events.fsm import *
from domain.signals import Signal

class TradingFSM:

    def __init__(self, symbol : str, current_state = State.FLAT):
        self.symbol = symbol
        self.current_state = current_state
        self.is_active = True
        self.strategies = []
        #Deafult limit for an asset qty if qty >= limit -> state = LONG.
        self.limit = 3
        if self.asset_qty() >= limit:
            self.current_state = State.LONG
        

    def on_event(self, event :Event):
        if isinstance(event, SignalEvent):
            self.on_signal(event.signal)
        elif isinstance(event, StateChange):
            pass
        elif isinstance(event, OrderResolved):
            pass

    def on_signal(self, signal : Signal):
        #AGREGAR VALIDACIONES.
        if signal is Signal.SELL:

            if self.current_state is State.LONG:
                pass
            elif self.current_state is State.FLAT:
                pass

        elif signal is Signal.BUY:
            
            if self.current_state is State.FLAT: 
                pass
            if self.current_state is State.LONG:
                print(f"Current TRADING_FSM {self.symbol} state: LONG.\nCannot buy more assets.")
    
    def validate_strategies(self):
        for s in strategies:
            if s.symbol is not self.symbol:
                raise Exception("THIS TRADING_FSM OBJECT IS NOT COMPATIBLE WITH A REGISTERED STRATEGY. (SYMBOL NOT COMPATIBLE)")

    def asset_qty(self):
        pass

    def set_limit(self, new_limit):
        self.limit = new_limit

    