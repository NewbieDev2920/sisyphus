from domain.ports.reporter_port import ReporterPort
from domain.events.event import Event
from domain.events.market import PriceUpdate
from domain.events.fsm import OrderResolved
import pandas as pd
import numpy as np
import os

class BacktestReporter(ReporterPort):
    def __init__(self, initial_cash=10000.0):
        self.initial_cash = initial_cash
        self.journal_entries = []
        self.trade_log = []  # List of trades executed
        self.equity_curve = []  # List of dicts {"timestamp": t, "cash": c, "lmv": l, "equity": e}

    def update(self, event: Event):
        # Implementar la interfaz requerida por el puerto
        if isinstance(event, PriceUpdate):
            # Generalmente no registramos cada PriceUpdate en el diario de texto para no hacerlo gigante,
            # pero podemos registrarlo si es necesario.
            pass
        elif isinstance(event, OrderResolved):
            entry = f"ORDER RESOLVED: ID={event.order_id}, Symbol={event.symbol}, Val={event.numeric_value}, Type={event.type}"
            self.journal_entries.append(entry)

    def journal(self) -> list:
        return self.journal_entries

    def log_trade(self, timestamp, symbol, side, qty, price, total_cost, cash_after):
        self.trade_log.append({
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "total_cost": total_cost,
            "cash_after": cash_after
        })
        self.journal_entries.append(
            f"[{timestamp}] TRADE {side} {qty:.4f} {symbol} @ ${price:.2f} (Cost/Rev: ${total_cost:.2f}, Cash: ${cash_after:.2f})"
        )

    def record_step(self, timestamp, cash, lmv, equity):
        self.equity_curve.append({
            "timestamp": timestamp,
            "cash": cash,
            "lmv": lmv,
            "equity": equity
        })

    def calculate_metrics(self) -> dict:
        if not self.equity_curve:
            return {
                "initial_equity": self.initial_cash,
                "final_equity": self.initial_cash,
                "total_return_pct": 0.0,
                "max_drawdown_pct": 0.0,
                "sharpe_ratio": 0.0,
                "total_trades": 0,
                "win_rate_pct": 0.0
            }

        df_eq = pd.DataFrame(self.equity_curve)
        df_eq["timestamp"] = pd.to_datetime(df_eq["timestamp"])
        df_eq.set_index("timestamp", inplace=True)
        
        initial_equity = self.initial_cash
        final_equity = df_eq["equity"].iloc[-1]
        total_return_pct = ((final_equity - initial_equity) / initial_equity) * 100.0

        # Max Drawdown
        df_eq["peak"] = df_eq["equity"].cummax()
        df_eq["drawdown"] = (df_eq["equity"] - df_eq["peak"]) / df_eq["peak"]
        max_dd_pct = df_eq["drawdown"].min() * 100.0
        
        df_eq["drawdown_dollars"] = df_eq["equity"] - df_eq["peak"]
        max_dd_dollars = abs(df_eq["drawdown_dollars"].min())

        # Sharpe Ratio 0% (SYMBOL VS BANK ACCOUNT (0%)) (diario aproximado)
        # Calculamos los retornos por paso
        df_eq["returns"] = df_eq["equity"].pct_change()
        mean_ret = df_eq["returns"].mean()
        std_ret = df_eq["returns"].std()
        downside_std_ret = (np.minimum(df_eq["returns"], 0)**2).mean()**0.5

        # Monthly Returns (Percentage and Dollars)
        try:
            monthly_eq = df_eq["equity"].resample("ME").last()
        except Exception:
            monthly_eq = df_eq["equity"].resample("M").last()
            
        monthly_mean_ret_pct = monthly_eq.pct_change().mean() * 100.0 if len(monthly_eq) > 1 else total_return_pct
        monthly_mean_ret_usd = monthly_eq.diff().mean() if len(monthly_eq) > 1 else (final_equity - initial_equity)

        #
        
        if std_ret > 0 and not np.isnan(std_ret):
            # Anualizado asumiendo pasos diarios (252). Si es por hora, se puede ajustar,
            # pero 252 es un estándar por defecto en finanzas.
            sharpe_ratio_0 = (mean_ret / std_ret) * np.sqrt(252)
        else:
            sharpe_ratio_0 = 0.0
        
        #Sortino Ratio
        if downside_std_ret > 0 and not np.isnan(downside_std_ret):
            sortino_ratio_0 = (mean_ret/downside_std_ret)*np.sqrt(252)
        else:
            sortino_ratio_0 = 0.0

        #Sharpe Ratio 8% (SYMBOL VS 1YR CDT BANCOLOMBIA)
        annual_rfr = 0.08
        daily_rfr = (1+annual_rfr)**(1/252)-1
        excess_returns = df_eq["returns"] - daily_rfr
        downside_std_ret = (np.minimum(df_eq["returns"]-daily_rfr, 0)**2).mean()**0.5

        if std_ret > 0 and not np.isnan(std_ret):
            sharpe_ratio_8 = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio_8 = 0.0

        if downside_std_ret > 0 and not np.isnan(downside_std_ret):
            sortino_ratio_8 = (excess_returns.mean()/downside_std_ret)*np.sqrt(252)
        else:
            sortino_ratio_8 = 0.0

        #Sharpe Ratio 12% (SYMBOL VS NEOBANCO)
        annual_rfr = 0.12
        daily_rfr = (1+annual_rfr)**(1/252)-1
        excess_returns = df_eq["returns"] - daily_rfr
        downside_std_ret = (np.minimum(df_eq["returns"]-daily_rfr, 0)**2).mean()**0.5

        if std_ret > 0 and not np.isnan(std_ret):
            sharpe_ratio_12 = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio_12 = 0.0

        if downside_std_ret > 0 and not np.isnan(downside_std_ret):
            sortino_ratio_12 = (excess_returns.mean()/downside_std_ret)*np.sqrt(252)
        else:
            sortino_ratio_12 = 0.0

        #Falta incluir Sortino y Sharpe ratio que compare con el SPY500

        # Calmar Ratio
        max_dd_fraction = abs(df_eq["drawdown"].min())
        years = len(df_eq) / 252.0
        cagr = ((final_equity / initial_equity) ** (1 / years) - 1) if years > 0 else 0.0
        calmar_ratio = (cagr / max_dd_fraction) if max_dd_fraction > 0 else (float('inf') if cagr > 0 else 0.0)

        # Recovery Factor
        net_profit = final_equity - initial_equity
        recovery_factor = (net_profit / max_dd_dollars) if max_dd_dollars > 0 else (float('inf') if net_profit > 0 else 0.0)

        # Win Rate a partir del log de operaciones
        # Para calcular el win rate, emparejamos compras y ventas del mismo activo.
        # Definición simple: si la venta generó más efectivo de lo que costó la compra.
        total_trades = len(self.trade_log)
        wins = 0
        losses = 0
        
        # Estrategia de emparejamiento FIFO simple para calcular trade win rate
        positions = {}  # symbol -> list of (qty, price)
        completed_trades_pnl = []

        for trade in self.trade_log:
            sym = trade["symbol"]
            side = trade["side"]
            qty = trade["qty"]
            price = trade["price"]

            if side == "BUY":
                if sym not in positions:
                    positions[sym] = []
                positions[sym].append({"qty": qty, "price": price})
            elif side == "SELL":
                sell_qty_remaining = qty
                trade_pnl = 0.0
                if sym in positions:
                    while sell_qty_remaining > 0 and positions[sym]:
                        buy_lot = positions[sym][0]
                        if buy_lot["qty"] <= sell_qty_remaining:
                            # Consumir el lote entero
                            trade_pnl += buy_lot["qty"] * (price - buy_lot["price"])
                            sell_qty_remaining -= buy_lot["qty"]
                            positions[sym].pop(0)
                        else:
                            # Consumir parte del lote
                            trade_pnl += sell_qty_remaining * (price - buy_lot["price"])
                            buy_lot["qty"] -= sell_qty_remaining
                            sell_qty_remaining = 0
                completed_trades_pnl.append(trade_pnl)

        wins_pnl = [pnl for pnl in completed_trades_pnl if pnl > 0]
        losses_pnl = [pnl for pnl in completed_trades_pnl if pnl < 0]
        
        wins = len(wins_pnl)
        losses = len(losses_pnl)
        completed_count = len(completed_trades_pnl)
        
        win_rate_pct = (wins / completed_count * 100.0) if completed_count > 0 else 0.0
        win_rate_frac = wins / completed_count if completed_count > 0 else 0.0
        loss_rate_frac = losses / completed_count if completed_count > 0 else 0.0

        avg_win = (sum(wins_pnl) / wins) if wins > 0 else 0.0
        avg_loss = abs(sum(losses_pnl) / losses) if losses > 0 else 0.0

        expectancy = (win_rate_frac * avg_win) - (loss_rate_frac * avg_loss)
        reward_to_risk = (avg_win / avg_loss) if avg_loss > 0 else (float('inf') if avg_win > 0 else 0.0)

        # PROFIT FACTOR
        gross_profit = sum(wins_pnl)
        gross_loss = abs(sum(losses_pnl))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0.0)

        # HISTORICAL VaR (95%, 1 day)
        if not df_eq["returns"].empty and not df_eq["returns"].isna().all():
            var_95_frac = df_eq["returns"].quantile(0.05)
            var_95_percent = abs(var_95_frac) * 100.0 if not np.isnan(var_95_frac) else 0.0
            var_95 = abs(var_95_frac) * final_equity if not np.isnan(var_95_frac) else 0.0
        else:
            var_95_percent = 0.0
            var_95 = 0.0

        #HISTORICAL VaR (99%, 1 day)
        if not df_eq["returns"].empty and not df_eq["returns"].isna().all():
            var_99_frac = df_eq["returns"].quantile(0.01)
            var_99_percent = abs(var_99_frac) * 100.0 if not np.isnan(var_99_frac) else 0.0
            var_99 = abs(var_99_frac) * final_equity if not np.isnan(var_99_frac) else 0.0
        else:
            var_99_percent = 0.0
            var_99 = 0.0

        return {
            "initial_equity": initial_equity,
            "final_equity": final_equity,
            "total_return_pct": total_return_pct,
            "max_drawdown_pct": max_dd_pct,
            "sharpe_ratio_0": sharpe_ratio_0,
            "sharpe_ratio_8": sharpe_ratio_8,
            "sharpe_ratio_12": sharpe_ratio_12,
            "sortino_ratio_0": sortino_ratio_0,
            "sortino_ratio_8": sortino_ratio_8,
            "sortino_ratio_12": sortino_ratio_12,
            "total_trades": total_trades,
            "completed_round_trips": completed_count,
            "win_rate_pct": win_rate_pct,
            "profit_factor": profit_factor,
            "calmar_ratio": calmar_ratio,
            "recovery_factor": recovery_factor,
            "expectancy": expectancy,
            "reward_to_risk": reward_to_risk,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "daily_mean_ret_pct": mean_ret * 100.0 if not np.isnan(mean_ret) else 0.0,
            "monthly_mean_ret_pct": monthly_mean_ret_pct if not np.isnan(monthly_mean_ret_pct) else 0.0,
            "monthly_mean_ret_usd": monthly_mean_ret_usd if not np.isnan(monthly_mean_ret_usd) else 0.0,
            "daily_std_ret_pct": std_ret * 100.0 if not np.isnan(std_ret) else 0.0,
            "annual_std_ret_pct": std_ret * np.sqrt(252) * 100.0 if not np.isnan(std_ret) else 0.0,
            "var_95": var_95,
            "var_95_percent": var_95_percent,
            "var_99":var_99,
            "var_99_percent":var_99_percent
        }

    def generate_report_text(self, symbol, strategy_name, start_date, end_date) -> str:
        metrics = self.calculate_metrics()
        
        trades_str = ""
        if self.trade_log:
            for t in self.trade_log:
                trades_str += f"[{t['timestamp']}] {t['side']} {t['qty']:.4f} @ ${t['price']:.2f} (Total: ${abs(t['total_cost']):.2f}, Cash: ${t['cash_after']:.2f})\n"
        else:
            trades_str = "No trades executed."

        report = f"""==================================================
SISYPHUS BACKTEST REPORT
==================================================
Asset Symbol:     {symbol}
Strategy:         {strategy_name}
Period:           {start_date} to {end_date}
==================================================
PERFORMANCE METRICS:
GENERAL: ----------------------------------------
Initial Cash:     ${metrics['initial_equity']:.2f}
Final Equity:     ${metrics['final_equity']:.2f}
Total Return:     {metrics['total_return_pct']:.2f}%
Max Drawdown:     {metrics['max_drawdown_pct']:.2f}%
Daily Mean (Ret): {metrics['daily_mean_ret_pct']:.4f}%
Monthly Mean (%): {metrics['monthly_mean_ret_pct']:.2f}%
Monthly Mean ($): ${metrics['monthly_mean_ret_usd']:.2f}
Daily Std (Vol):  {metrics['daily_std_ret_pct']:.4f}%
Annual Std (Vol): {metrics['annual_std_ret_pct']:.4f}%
RISK EVALUATION & CONTRAST: ---------------------
Historical VaR 95% (1d): ${metrics.get('var_95', 0.0):.2f} ({metrics.get('var_95_percent', 0.0):.2f}%)
Historical VaR 99% (1d): ${metrics.get('var_99',0.0):.2f} ({metrics.get('var_99_percent', 0.0):.2f}%)
Sharpe Ratio {symbol} VS 0%:  {metrics['sharpe_ratio_0']:.4f}
Sharpe Ratio {symbol} VS 8%:  {metrics['sharpe_ratio_8']:.4f}
Sharpe Ratio {symbol} VS 12%: {metrics['sharpe_ratio_12']:.4f}
:-:-:-:-:-:-:
Sortino Ratio {symbol} VS 0%:  {metrics['sortino_ratio_0']:.4f}
Sortino Ratio {symbol} VS 8%:  {metrics['sortino_ratio_8']:.4f}
Sortino Ratio {symbol} VS 12%: {metrics['sortino_ratio_12']:.4f}
:-:-:-:-:-:-:
Calmar Ratio:                  {metrics['calmar_ratio']:.4f}
Recovery Factor:               {metrics['recovery_factor']:.4f}
TRADE ANALYSIS: ---------------------------------
Total Orders:     {metrics['total_trades']}
Closed Trades:    {metrics['completed_round_trips']}
Win Rate:         {metrics['win_rate_pct']:.2f}%
Profit Factor:    {metrics['profit_factor']:.2f}
Expectancy (Trade):${metrics['expectancy']:.2f}
R:R Ratio:        1:{metrics['reward_to_risk']:.2f}
==================================================
TRANSACTION JOURNAL:
--------------------------------------------------
{trades_str}
==================================================
"""
        return report

    def save_report_to_file(self, symbol, strategy_name, start_date, end_date, reports_dir="reports/backtests") -> str:
        os.makedirs(reports_dir, exist_ok=True)
        # Formatear nombre del archivo
        import datetime
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{strategy_name}_{symbol}_{timestamp_str}.txt"
        file_path = os.path.join(reports_dir, filename)
        
        report_text = self.generate_report_text(symbol, strategy_name, start_date, end_date)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        return file_path
