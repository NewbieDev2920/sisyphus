import os
import pandas as pd
import numpy as np
import glob
from infrastructure.market_data.cached_historical_market_data import CachedHistoricalMarketData
from infrastructure.account.simulated_account import SimulatedAccount
from infrastructure.simulated_executor import SimulatedExecutor
from infrastructure.reporters.backtest_reporter import BacktestReporter
from domain.ports.fsm.trading_fsm import TradingFSM
from domain.events.market import PriceUpdate
from domain.signals import Signal

from domain.strategies.basic.monotonic_increasing import MonotonicIncreasing
from domain.strategies.basic.floor import Floor
from domain.strategies.basic.manual import Manual
from domain.strategies.statistical_inference.downside_momentum_risk import DownsideMomentumRisk

STRATEGY_MAP = {
    "MonotonicIncreasing": MonotonicIncreasing,
    "Floor": Floor,
    "Manual": Manual
}

class BacktestService:
    def __init__(self, cache_dir="data/historical", reports_dir="reports/backtests", plots_dir="reports/plots"):
        self.data_provider = CachedHistoricalMarketData(cache_dir=cache_dir)
        self.reports_dir = reports_dir
        self.plots_dir = plots_dir
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)

    def run_backtest(self, strategy_name: str, symbol: str, start_date: str, end_date: str, interval: str = "1d", initial_cash: float = 10000.0) -> tuple:
        initial_cash = float(initial_cash)
        if strategy_name not in STRATEGY_MAP:
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {list(STRATEGY_MAP.keys())}")
            
        strategy_class = STRATEGY_MAP[strategy_name]
        
        # 1. Obtener datos históricos
        df = self.data_provider.get_symbol_time_series(symbol, period=None, interval=interval, start=start_date, end=end_date)
        if df is None or df.empty:
            raise ValueError(f"No historical data found for {symbol} in range {start_date} to {end_date} with interval '{interval}'")

        # 2. Inicializar entorno simulado
        account = SimulatedAccount(initial_cash=initial_cash)
        executor = SimulatedExecutor(account=account, slippage_pct=0.0005, commission=1.0)
        reporter = BacktestReporter(initial_cash=initial_cash)
        
        fsm = TradingFSM(symbol, account, bot_bp=initial_cash, executor=executor, destiny_channel= None)
        executor.register_fsm(fsm)
        
        # Instanciar estrategia inyectando el FSM
        strategy = strategy_class(symbol, fsm=fsm)
        fsm.strategies.append(strategy)

        # 3. Bucle de Simulación
        last_trade_index = 0
        
        for timestamp, row in df.iterrows():
            price = float(row["Close"])
            if pd.isna(price):
                continue
                
            # Actualizar precios en adaptadores simulados antes del paso
            account.set_current_price(symbol, price)
            executor.set_current_price(symbol, price)
            
            # Crear y enviar PriceUpdate
            price_update = PriceUpdate(price, symbol)
            fsm.on_event(price_update)
            strategy.update(price_update)
            
            # Registrar transacciones ejecutadas en este paso
            for trade in executor.trade_events[last_trade_index:]:
                reporter.log_trade(
                    timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol=trade["symbol"],
                    side=trade["side"],
                    qty=trade["qty"],
                    price=trade["price"],
                    total_cost=trade["total_cost"],
                    cash_after=trade["cash_after"]
                )
            last_trade_index = len(executor.trade_events)
            
            # Registrar evolución de balance al final del tick
            reporter.record_step(
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                cash=account.cash,
                lmv=account.long_market_value,
                equity=account.equity
            )

        # 4. Guardar reporte a archivo de texto
        report_path = reporter.save_report_to_file(symbol, strategy_name, start_date, end_date, self.reports_dir)
        
        # 5. Graficar resultados usando el graph_generator.py de infraestructura
        plot_path = self._generate_plot(df, reporter, symbol, strategy_name)
        
        # Calcular resumen de métricas
        metrics = reporter.calculate_metrics()
        summary_text = (
            f"Initial Cash: ${metrics['initial_equity']:.2f}\n"
            f"Final Equity: ${metrics['final_equity']:.2f}\n"
            f"Total Return: {metrics['total_return_pct']:.2f}%\n"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%\n"
            f"Daily Mean:   {metrics['daily_mean_ret_pct']:.4f}%\n"
            f"Monthly Mean: {metrics['monthly_mean_ret_pct']:.2f}% (${metrics['monthly_mean_ret_usd']:.2f})\n"
            f"Daily Vol:    {metrics['daily_std_ret_pct']:.4f}%\n"
            f"Annual Vol:   {metrics['annual_std_ret_pct']:.4f}%\n"
            f"Total Orders: {metrics['total_trades']}\n"
            f"Win Rate:     {metrics['win_rate_pct']:.2f}%\n"
            f"Profit Factor:  {metrics['profit_factor']:.2f}\n"
            f"Calmar Ratio:   {metrics['calmar_ratio']:.4f}\n"
            f"Recovery Factor:{metrics['recovery_factor']:.4f}\n"
            f"Expectancy:     ${metrics['expectancy']:.2f}\n"
            f"R:R Ratio:      1:{metrics['reward_to_risk']:.2f}\n"
            f"Hist VaR(95%,1d): ${metrics.get('var_95', 0.0):.2f} ({metrics.get('var_95_percent', 0.0):.2f}%)"
        )
        
        return report_path, plot_path, summary_text

    def run_manual_backtest(self, symbol: str, start_date: str, end_date: str, interval: str = "1d", initial_cash: float = 10000.0, qty: float = None, notional: float = None) -> tuple:
        initial_cash = float(initial_cash)
        if qty is not None:
            qty = float(qty)
        if notional is not None:
            notional = float(notional)
            
        if qty is None and notional is None:
            raise ValueError("Must specify either 'qty' or 'notional' for a manual backtest.")
            
        # 1. Obtener datos históricos
        df = self.data_provider.get_symbol_time_series(symbol, period=None, interval=interval, start=start_date, end=end_date)
        if df is None or df.empty:
            raise ValueError(f"No historical data found for {symbol} in range {start_date} to {end_date} with interval '{interval}'")

        # 2. Inicializar entorno simulado
        account = SimulatedAccount(initial_cash=initial_cash)
        executor = SimulatedExecutor(account=account, slippage_pct=0.0005, commission=1.0)
        reporter = BacktestReporter(initial_cash=initial_cash)
        
        fsm = TradingFSM(symbol, account, bot_bp=initial_cash, executor=executor, destiny_channel= None)
        executor.register_fsm(fsm)
        
        # Instanciar estrategia manual
        strategy = Manual(symbol, fsm=fsm)
        fsm.strategies.append(strategy)

        # 3. Bucle de Simulación
        last_trade_index = 0
        total_steps = len(df)
        step_idx = 0
        
        for timestamp, row in df.iterrows():
            price = float(row["Close"])
            if pd.isna(price):
                continue
                
            # Actualizar precios en adaptadores simulados antes del paso
            account.set_current_price(symbol, price)
            executor.set_current_price(symbol, price)
            
            # Crear y enviar PriceUpdate
            price_update = PriceUpdate(price, symbol)
            fsm.on_event(price_update)
            strategy.update(price_update)
            
            # En la primera vela, ejecutar la compra manual
            if step_idx == 0:
                if qty is not None:
                    strategy.buy(qty)
                elif notional is not None:
                    strategy.buy_notional(notional)
            
            # En la última vela, cerrar la posición vendiéndolo todo
            elif step_idx == total_steps - 1:
                owned_qty = account.get_position_qty(symbol)
                if owned_qty > 0:
                    strategy.sell(owned_qty)
            
            step_idx += 1
            
            # Registrar transacciones ejecutadas en este paso
            for trade in executor.trade_events[last_trade_index:]:
                reporter.log_trade(
                    timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol=trade["symbol"],
                    side=trade["side"],
                    qty=trade["qty"],
                    price=trade["price"],
                    total_cost=trade["total_cost"],
                    cash_after=trade["cash_after"]
                )
            last_trade_index = len(executor.trade_events)
            
            # Registrar evolución de balance al final del tick
            reporter.record_step(
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                cash=account.cash,
                lmv=account.long_market_value,
                equity=account.equity
            )

        # 4. Guardar reporte a archivo de texto
        report_path = reporter.save_report_to_file(symbol, "Manual", start_date, end_date, self.reports_dir)
        
        # 5. Graficar resultados usando el graph_generator.py de infraestructura
        plot_path = self._generate_plot(df, reporter, symbol, "Manual")
        
        # Calcular resumen de métricas
        metrics = reporter.calculate_metrics()
        summary_text = (
            f"Initial Cash: ${metrics['initial_equity']:.2f}\n"
            f"Final Equity: ${metrics['final_equity']:.2f}\n"
            f"Total Return: {metrics['total_return_pct']:.2f}%\n"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%\n"
            f"Daily Mean:   {metrics['daily_mean_ret_pct']:.4f}%\n"
            f"Monthly Mean: {metrics['monthly_mean_ret_pct']:.2f}% (${metrics['monthly_mean_ret_usd']:.2f})\n"
            f"Daily Vol:    {metrics['daily_std_ret_pct']:.4f}%\n"
            f"Annual Vol:   {metrics['annual_std_ret_pct']:.4f}%\n"
            f"Total Orders: {metrics['total_trades']}\n"
            f"Win Rate:     {metrics['win_rate_pct']:.2f}%\n"
            f"Profit Factor:  {metrics['profit_factor']:.2f}\n"
            f"Calmar Ratio:   {metrics['calmar_ratio']:.4f}\n"
            f"Hist VaR(95%,1d): ${metrics.get('var_95', 0.0):.2f} ({metrics.get('var_95_percent', 0.0):.2f}%)"
        )
        
        return report_path, plot_path, summary_text

    def run_floor_backtest(self, symbol: str, start_date: str, end_date: str, floor_price: float, interval: str = "1d", initial_cash: float = 10000.0, qty: float = None, notional: float = None) -> tuple:
        initial_cash = float(initial_cash)
        floor_price = float(floor_price)
        if qty is not None:
            qty = float(qty)
        if notional is not None:
            notional = float(notional)
            
        if qty is None and notional is None:
            raise ValueError("Must specify either 'qty' or 'notional' for a floor backtest to buy the initial position.")
            
        # 1. Obtener datos históricos
        df = self.data_provider.get_symbol_time_series(symbol, period=None, interval=interval, start=start_date, end=end_date)
        if df is None or df.empty:
            raise ValueError(f"No historical data found for {symbol} in range {start_date} to {end_date} with interval '{interval}'")

        # 2. Inicializar entorno simulado
        account = SimulatedAccount(initial_cash=initial_cash)
        executor = SimulatedExecutor(account=account, slippage_pct=0.0005, commission=1.0)
        reporter = BacktestReporter(initial_cash=initial_cash)
        
        fsm = TradingFSM(symbol, account, bot_bp=initial_cash, executor=executor, destiny_channel= None)
        executor.register_fsm(fsm)
        
        # Instanciar estrategia floor
        strategy = Floor(symbol, fsm=fsm, floor_price=floor_price)
        fsm.strategies.append(strategy)

        # 3. Bucle de Simulación
        last_trade_index = 0
        total_steps = len(df)
        step_idx = 0
        
        for timestamp, row in df.iterrows():
            price = float(row["Close"])
            if pd.isna(price):
                continue
                
            # Actualizar precios en adaptadores simulados antes del paso
            account.set_current_price(symbol, price)
            executor.set_current_price(symbol, price)
            
            # Crear y enviar PriceUpdate a la FSM
            price_update = PriceUpdate(price, symbol)
            
            # En la primera vela, ejecutar la compra inicial para tener posición
            if step_idx == 0:
                if qty is not None:
                    strategy.compute_signal(Signal.BUY, qty)
                elif notional is not None:
                    strategy.compute_signal(Signal.BUY_NOTIONAL, notional)
                    
            fsm.on_event(price_update)
            strategy.update(price_update)
            
            # En la última vela, si sigue abierta la posición, cerrarla
            if step_idx == total_steps - 1:
                owned_qty = account.get_position_qty(symbol)
                if owned_qty > 0:
                    strategy.compute_signal(Signal.SELL, owned_qty)
            
            step_idx += 1
            
            # Registrar transacciones ejecutadas en este paso
            for trade in executor.trade_events[last_trade_index:]:
                reporter.log_trade(
                    timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol=trade["symbol"],
                    side=trade["side"],
                    qty=trade["qty"],
                    price=trade["price"],
                    total_cost=trade["total_cost"],
                    cash_after=trade["cash_after"]
                )
            last_trade_index = len(executor.trade_events)
            
            # Registrar evolución de balance al final del tick
            reporter.record_step(
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                cash=account.cash,
                lmv=account.long_market_value,
                equity=account.equity
            )

        # 4. Guardar reporte a archivo de texto
        report_path = reporter.save_report_to_file(symbol, "Floor", start_date, end_date, self.reports_dir)
        
        # 5. Graficar resultados usando el graph_generator.py de infraestructura
        plot_path = self._generate_plot(df, reporter, symbol, "Floor")
        
        # Calcular resumen de métricas
        metrics = reporter.calculate_metrics()
        summary_text = (
            f"Initial Cash: ${metrics['initial_equity']:.2f}\n"
            f"Final Equity: ${metrics['final_equity']:.2f}\n"
            f"Total Return: {metrics['total_return_pct']:.2f}%\n"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%\n"
            f"Daily Mean:   {metrics['daily_mean_ret_pct']:.4f}%\n"
            f"Monthly Mean: {metrics['monthly_mean_ret_pct']:.2f}% (${metrics['monthly_mean_ret_usd']:.2f})\n"
            f"Daily Vol:    {metrics['daily_std_ret_pct']:.4f}%\n"
            f"Annual Vol:   {metrics['annual_std_ret_pct']:.4f}%\n"
            f"Total Orders: {metrics['total_trades']}\n"
            f"Win Rate:     {metrics['win_rate_pct']:.2f}%\n"
            f"Profit Factor:  {metrics['profit_factor']:.2f}\n"
            f"Calmar Ratio:   {metrics['calmar_ratio']:.4f}\n"
            f"Hist VaR(95%,1d): ${metrics.get('var_95', 0.0):.2f} ({metrics.get('var_95_percent', 0.0):.2f}%)"
        )
        
        return report_path, plot_path, summary_text

    def run_downside_momentum_risk_backtest(self, symbol: str, start_date: str, end_date: str, short_alpha: float, long_alpha: float, threshold: float, interval: str = "1d", initial_cash: float = 10000.0, qty: float = None, notional: float = None) -> tuple:
        initial_cash = float(initial_cash)
        if qty is not None:
            qty = float(qty)
        if notional is not None:
            notional = float(notional)
            
        if qty is None and notional is None:
            raise ValueError("Must specify either 'qty' or 'notional' for a downside momentum risk backtest to buy the initial position.")
        
        # 1. Obtener datos históricos
        df = self.data_provider.get_symbol_time_series(symbol, period=None, interval=interval, start=start_date, end=end_date)
        if df is None or df.empty:
            raise ValueError(f"No historical data found for {symbol} in range {start_date} to {end_date} with interval '{interval}'")

        # 2. Inicializar entorno simulado
        account = SimulatedAccount(initial_cash=initial_cash)
        executor = SimulatedExecutor(account=account, slippage_pct=0.0005, commission=1.0)
        reporter = BacktestReporter(initial_cash=initial_cash)
        
        fsm = TradingFSM(symbol, account, bot_bp=initial_cash, executor=executor, destiny_channel= None)
        executor.register_fsm(fsm)
        
        # Instanciar estrategia
        strategy = DownsideMomentumRisk(symbol, fsm, short_alpha=short_alpha, long_alpha=long_alpha, threshold=threshold)
        fsm.strategies.append(strategy)

        # 3. Bucle de Simulación
        last_trade_index = 0
        ewma_s_history = []
        ewma_l_history = []
        total_steps = len(df)
        step_idx = 0
        
        for timestamp, row in df.iterrows():
            price = float(row["Close"])
            if pd.isna(price):
                ewma_s_history.append(ewma_s_history[-1] if ewma_s_history else 0)
                ewma_l_history.append(ewma_l_history[-1] if ewma_l_history else 0)
                continue
                
            # Actualizar precios en adaptadores simulados antes del paso
            account.set_current_price(symbol, price)
            executor.set_current_price(symbol, price)
            
            # Crear y enviar PriceUpdate a la FSM
            price_update = PriceUpdate(price, symbol)
            
            # En la primera vela, ejecutar la compra inicial para tener posición
            if step_idx == 0:
                if qty is not None:
                    strategy.compute_signal(Signal.BUY, qty)
                elif notional is not None:
                    strategy.compute_signal(Signal.BUY_NOTIONAL, notional)
                    
            fsm.on_event(price_update)
            strategy.update(price_update)
            
            ewma_s_history.append(strategy.ewma_s)
            ewma_l_history.append(strategy.ewma_l)
            
            # En la última vela, si sigue abierta la posición, cerrarla para ver resultado final
            if step_idx == total_steps - 1:
                owned_qty = account.get_position_qty(symbol)
                if owned_qty > 0:
                    strategy.compute_signal(Signal.SELL, owned_qty)
                    
            step_idx += 1
            
            # Registrar transacciones ejecutadas en este paso
            for trade in executor.trade_events[last_trade_index:]:
                reporter.log_trade(
                    timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    symbol=trade["symbol"],
                    side=trade["side"],
                    qty=trade["qty"],
                    price=trade["price"],
                    total_cost=trade["total_cost"],
                    cash_after=trade["cash_after"]
                )
            last_trade_index = len(executor.trade_events)
            
            # Registrar evolución de balance al final del tick
            reporter.record_step(
                timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                cash=account.cash,
                lmv=account.long_market_value,
                equity=account.equity
            )

        # 4. Guardar reporte a archivo de texto
        report_path = reporter.save_report_to_file(symbol, "DownsideMomentumRisk", start_date, end_date, self.reports_dir)
        
        # 5. Graficar resultados específicos de esta estrategia
        plot_path = self._generate_downside_plot(df, ewma_s_history, ewma_l_history, symbol)
        
        # Calcular resumen de métricas
        metrics = reporter.calculate_metrics()
        summary_text = (
            f"Initial Cash: ${metrics['initial_equity']:.2f}\n"
            f"Final Equity: ${metrics['final_equity']:.2f}\n"
            f"Total Return: {metrics['total_return_pct']:.2f}%\n"
            f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%\n"
            f"Daily Mean:   {metrics['daily_mean_ret_pct']:.4f}%\n"
            f"Monthly Mean: {metrics['monthly_mean_ret_pct']:.2f}% (${metrics['monthly_mean_ret_usd']:.2f})\n"
            f"Daily Vol:    {metrics['daily_std_ret_pct']:.4f}%\n"
            f"Annual Vol:   {metrics['annual_std_ret_pct']:.4f}%\n"
            f"Total Orders: {metrics['total_trades']}\n"
            f"Win Rate:     {metrics['win_rate_pct']:.2f}%\n"
            f"Profit Factor:  {metrics['profit_factor']:.2f}\n"
            f"Calmar Ratio:   {metrics['calmar_ratio']:.4f}\n"
            f"Hist VaR(95%,1d): ${metrics.get('var_95', 0.0):.2f} ({metrics.get('var_95_percent', 0.0):.2f}%)"
        )
        
        return report_path, plot_path, summary_text

    def _generate_downside_plot(self, df: pd.DataFrame, ewma_s_history: list, ewma_l_history: list, symbol: str) -> str:
        from infrastructure.plotter.graph_generator import GraphGenerator
        from infrastructure.plotter.visual_function import VisualFunction
        from domain.ports.graph.function_type import FunctionType
        
        graph_gen = GraphGenerator(self.plots_dir + "/")
        domain = np.arange(len(df))
        
        f_ewma_s = VisualFunction(
            name="EWMA Short (Corto Plazo)",
            ftype=FunctionType.LINE_SEGMENTS,
            sampled_data={"domain": domain, "range": lambda x: np.array([ewma_s_history[int(v)] for v in x])},
            color="#EF4444" # Rojo
        )
        
        f_ewma_l = VisualFunction(
            name="EWMA Long (Largo Plazo)",
            ftype=FunctionType.LINE_SEGMENTS,
            sampled_data={"domain": domain, "range": lambda x: np.array([ewma_l_history[int(v)] for v in x])},
            color="#3B82F6" # Azul
        )

        title = f"Downside Momentum Risk (EWMA Crossover) - {symbol}"
        graph_gen.plot_in_R2([f_ewma_s, f_ewma_l], title=title)
        
        # Encontrar el archivo guardado más reciente en plots_dir
        import glob
        files = glob.glob(os.path.join(self.plots_dir, "*.jpg"))
        if not files:
            raise FileNotFoundError("No se encontró la imagen generada por GraphGenerator en la ruta configurada.")
            
        latest_file = max(files, key=os.path.getctime)
        return latest_file

    def _generate_plot(self, df: pd.DataFrame, reporter: BacktestReporter, symbol: str, strategy_name: str) -> str:
        from infrastructure.plotter.graph_generator import GraphGenerator
        from infrastructure.plotter.visual_function import VisualFunction
        from domain.ports.graph.function_type import FunctionType
        
        # Instanciar generador apuntando al directorio de gráficos de reportes
        graph_gen = GraphGenerator(self.plots_dir + "/")
        
        df_eq = pd.DataFrame(reporter.equity_curve)
        domain = np.arange(len(df_eq))
        
        # Datos de la curva de equidad
        equity_vals = df_eq["equity"].values
        price_vals = df["Close"].values[:len(equity_vals)]
        
        f_equity = VisualFunction(
            name="Portfolio Equity ($)",
            ftype=FunctionType.LINE_SEGMENTS,
            sampled_data={"domain": domain, "range": lambda x: np.array([equity_vals[int(val)] for val in x])},
            color="#3B82F6"
        )
        
        # Punto de referencia: Buy and Hold del activo subyacente
        initial_price = price_vals[0] if len(price_vals) > 0 else 1.0
        benchmark_vals = (price_vals / initial_price) * reporter.initial_cash
        f_benchmark = VisualFunction(
            name=f"{symbol} Buy & Hold ($)",
            ftype=FunctionType.LINE_SEGMENTS,
            sampled_data={"domain": domain, "range": lambda x: np.array([benchmark_vals[int(val)] for val in x])},
            color="#9CA3AF"
        )
        
        # Sombreado de estado de exposición (LONG verde / FLAT rojo)
        exposure_vals = np.array([1 if d["lmv"] > 0 else 0 for d in reporter.equity_curve])
        f_exposure = VisualFunction(
            name="Exposure",
            ftype=FunctionType.SHADED_STEP,
            sampled_data={"domain": domain, "range": pd.Series(exposure_vals)},
            color="#10B981"
        )
        
        title = f"Backtest {strategy_name} on {symbol}"
        
        # Extraer los retornos diarios para el histograma, en porcentaje (%)
        returns_pct = df_eq["equity"].pct_change().dropna().values * 100.0
        
        equity_vals = df_eq["equity"].values
        mu_eq = equity_vals.mean() if len(equity_vals) > 0 else 0
        sigma_eq = equity_vals.std() if len(equity_vals) > 0 else 0
        extra_legend = f"$\mu$ = {mu_eq:.2f}\n$\sigma$ = {sigma_eq:.2f}"
        
        graph_gen.plot_time_series_with_hist([f_equity, f_benchmark, f_exposure], returns_pct, title, extra_legend=extra_legend)
        
        # Encontrar el archivo guardado más reciente en plots_dir
        files = glob.glob(os.path.join(self.plots_dir, "*.jpg"))
        if not files:
            raise FileNotFoundError("No se encontró la imagen generada por GraphGenerator en la ruta configurada.")
            
        latest_file = max(files, key=os.path.getctime)
        return latest_file
