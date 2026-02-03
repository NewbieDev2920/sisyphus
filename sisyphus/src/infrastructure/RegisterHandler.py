from domain.ports.register_handler_port import RegisterHandlerPort
import json
from domain.strategies.manual import Manual
from domain.ports.fsm.trading_fsm import TradingFSM
from application.order_placer_service import OrderPlacerService
from infrastructure.account.alpaca_account import AlpacaAccount
from infrastructure.SisyphusExe import SisyphusExe
"""
fsm = TradingFSM(symbol, alpaca_account, bot_bp=10000.0, executor=executor)
    strategy = Manual(symbol, fsm)
    order_placer_service.subscribe_manual(strategy)
"""

class RegisterHandler(RegisterHandlerPort):

    def __init__(self, config_path, order_placer_service : OrderPlacerService, alpaca_account : AlpacaAccount, executor : SisyphusExe, registered_symbols, registered_fsm ):
        self.path = config_path
        self.order_placer_service = order_placer_service
        self.alpaca_account = alpaca_account
        self.executor = executor
        self.registered_symbols =registered_symbols
        self.registered_fsm = registered_fsm
    
    def register_symbol(self, symbol):
        # Read existing config
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {"registered_symbols": []}

        # Modify
        if symbol not in config["registered_symbols"]:
            config["registered_symbols"].append(symbol)
        
        # Write back
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        fsm = TradingFSM(symbol, self.alpaca_account, bot_bp= 10000.0, executor = self.executor)
        self.registered_fsm.append(fsm)
        manual = Manual(symbol,fsm)
        self.order_placer_service.subscribe_manual(manual)
        self.registered_symbols.append(symbol)

    def unregister_symbol(self, symbol):
        # Read existing config
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return # Nothing to unregister
            
        # Modify
        try:
            if symbol in config["registered_symbols"]:
                config["registered_symbols"].remove(symbol)
        except Exception as e:
            print(f"An error has occured while updating config: {e}")
            
        # Write back
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        self.order_placer_service.unsubscribe_manual(symbol)
        self.registered_symbols.remove(symbol)
        for fsm in self.registered_fsm:
            if fsm.symbol == symbol:
                self.registered_fsm.remove(fsm)

    def registration_list(self):
        return str(self.registered_symbols)

    def fsm_status(self):
        final_msg = ""
        for fsm in self.registered_fsm:
            msg = f"""
            ---------------------
            |FSM : {fsm.symbol}
            ----------------------
            | CURRENT STATE : {fsm.current_state}
            | QTY LIMIT : {fsm.limit}
            | IS ACTIVE : {fsm.is_active}
            | CURRENT QTY : IMPLEMENTATION SOON
            ---------------------
            |ASSOCIATED STRATEGIES
            ----------------------
            """
            strategies_msg = "\n"
            for strat in fsm.strategies:
                strategies_msg = strategies_msg+"* "+strat.name+"\n"
            final_msg = final_msg+msg+strategies_msg

        return final_msg
