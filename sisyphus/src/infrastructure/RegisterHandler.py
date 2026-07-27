from domain.ports.register_handler_port import RegisterHandlerPort
import json
from domain.ports.fsm.trading_fsm import TradingFSM
from application.order_placer_service import OrderPlacerService
from infrastructure.account.alpaca_account import AlpacaAccount
from infrastructure.SisyphusExe import SisyphusExe
from infrastructure.console_handler import get_console_handler
from infrastructure.feeders.interval_feeder import IntervalFeeder
from domain.events.market import PriceUpdate

# Strategies
from domain.strategies.basic.monotonic_increasing import MonotonicIncreasing
from domain.strategies.basic.floor import Floor
from domain.strategies.basic.manual import Manual
from domain.strategies.statistical_inference.downside_momentum_risk import DownsideMomentumRisk

STRATEGY_MAP = {
    "MonotonicIncreasing": MonotonicIncreasing,
    "Floor": Floor,
    "Manual": Manual,
    "DownsideMomentumRisk": DownsideMomentumRisk
}

class RegisterHandler(RegisterHandlerPort):

    def __init__(self, config_path, order_placer_service: OrderPlacerService, alpaca_account: AlpacaAccount, executor: SisyphusExe, registered_symbols, registered_fsm):
        self.path = config_path
        self.order_placer_service = order_placer_service
        self.alpaca_account = alpaca_account
        self.executor = executor
        
        # registered_symbols here is passed from main.py (as a dict of fsm_configs)
        self.registered_symbols = registered_symbols if registered_symbols is not None else {}
        self.registered_fsm = registered_fsm
        
        self.active_feeders = {} # symbol -> {strategy_name -> IntervalFeeder}

    def _read_config(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"fsm_configs": {}}

    def _write_config(self, config):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    def register_symbol(self, symbol):
        config = self._read_config()
        if "fsm_configs" not in config:
            config["fsm_configs"] = {}

        if symbol not in config["fsm_configs"]:
            config["fsm_configs"][symbol] = []

        self._write_config(config)

        fsm = TradingFSM(symbol, self.alpaca_account, bot_bp=10000.0, executor=self.executor, destiny_channel=None)
        self.registered_fsm.append(fsm)
        self.registered_symbols[symbol] = config["fsm_configs"][symbol]
        
        if symbol not in self.active_feeders:
            self.active_feeders[symbol] = {}

    def unregister_symbol(self, symbol):
        config = self._read_config()
        if "fsm_configs" in config and symbol in config["fsm_configs"]:
            del config["fsm_configs"][symbol]
            self._write_config(config)

        # Cleanup Memory (Feeders and FSM)
        if symbol in self.active_feeders:
            for strat_name, feeder in self.active_feeders[symbol].items():
                if self.order_placer_service.real_time_market_data:
                    try:
                        self.order_placer_service.real_time_market_data.observers[symbol].remove(feeder)
                    except ValueError:
                        pass
            del self.active_feeders[symbol]

        fsm = self.get_fsm(symbol)
        if fsm:
            self.registered_fsm.remove(fsm)

        if symbol in self.registered_symbols:
            del self.registered_symbols[symbol]

    def get_fsm(self, symbol: str):
        for fsm in self.registered_fsm:
            if fsm.symbol == symbol:
                return fsm
        return None

    def instance_strategy(self, symbol: str, strategy_name: str, interval_seconds: int, params: dict):
        fsm = self.get_fsm(symbol)
        if not fsm:
            raise ValueError(f"No FSM registered for {symbol}")

        if strategy_name not in STRATEGY_MAP:
            raise ValueError(f"Strategy {strategy_name} not found")

        strategy_class = STRATEGY_MAP[strategy_name]
        
        # Instantiate strategy
        strategy = strategy_class(symbol, fsm, **params)
        
        # Create Interval Feeder and wrap strategy update
        def wrapped_callback(parsed_value):
            strategy.update(PriceUpdate(parsed_value, symbol))

        feeder = IntervalFeeder(symbol=symbol, interval_seconds=interval_seconds, strategy_callback=wrapped_callback)
        
        # Add feeder as observer to WebSocket
        if self.order_placer_service.real_time_market_data:
            self.order_placer_service.real_time_market_data.append_observer(feeder)
        
        # Append to FSM and active feeders
        fsm.add_strategy(strategy)
        if strategy_name == "Manual":
            self.order_placer_service.subscribe_manual(strategy)
        if symbol not in self.active_feeders:
            self.active_feeders[symbol] = {}
        self.active_feeders[symbol][strategy_name] = feeder

        # Save to config
        config = self._read_config()
        if "fsm_configs" not in config:
            config["fsm_configs"] = {}
        if symbol not in config["fsm_configs"]:
            config["fsm_configs"][symbol] = []
            
        # Check if strategy already exists in config, remove it to update
        config["fsm_configs"][symbol] = [s for s in config["fsm_configs"][symbol] if s.get("name") != strategy_name]
        
        config["fsm_configs"][symbol].append({
            "name": strategy_name,
            "interval_seconds": interval_seconds,
            "params": params
        })
        self._write_config(config)

    def terminate_strategy(self, symbol: str, strategy_name: str):
        fsm = self.get_fsm(symbol)
        if not fsm:
            raise ValueError(f"No FSM registered for {symbol}")

        # Remove Feeder
        if symbol in self.active_feeders and strategy_name in self.active_feeders[symbol]:
            feeder = self.active_feeders[symbol][strategy_name]
            if self.order_placer_service.real_time_market_data:
                try:
                    self.order_placer_service.real_time_market_data.observers[symbol].remove(feeder)
                except ValueError:
                    pass
            del self.active_feeders[symbol][strategy_name]

        # Remove from FSM
        fsm.remove_strategy(strategy_name)
        if strategy_name == "Manual":
            self.order_placer_service.unsubscribe_manual(symbol)

        # Update config
        config = self._read_config()
        if "fsm_configs" in config and symbol in config["fsm_configs"]:
            config["fsm_configs"][symbol] = [s for s in config["fsm_configs"][symbol] if s.get("name") != strategy_name]
            self._write_config(config)

    def registration_list(self):
        return str(list(self.registered_symbols.keys()))

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
            | CURRENT QTY : {fsm.current_qty}
            ---------------------
            |ASSOCIATED STRATEGIES
            ----------------------
            """
            strategies_msg = "\n"
            for strat in fsm.strategies:
                strategies_msg = strategies_msg+"* "+strat.name+"\n"
            final_msg = final_msg+msg+strategies_msg
        return final_msg

    def fsm_config_maps(self):
        final_msg = ""
        for fsm in self.registered_fsm:
            msg = f"""
            ---------------------
            |FSM : {fsm.symbol}
            ----------------------
            | CONFIG MAPS
            ----------------------
            """
            strategies_msg = "\n"
            for strat in fsm.strategies:
                if hasattr(strat, "configuration_map"):
                    strategies_msg += f"* {strat.name}:\n {strat.configuration_map()}\n"
                else:
                    strategies_msg += f"* {strat.name}: No configuration map available.\n"
            final_msg += msg + strategies_msg

        if not final_msg:
            return "No registered FSMs or strategies."
        return final_msg
