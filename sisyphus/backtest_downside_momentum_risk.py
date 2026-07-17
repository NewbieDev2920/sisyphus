import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

# Configurar stdout para soportar caracteres Unicode (emojis) en Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Añadir src al path para poder importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from infrastructure.market_data.cached_historical_market_data import CachedHistoricalMarketData
from infrastructure.account.simulated_account import SimulatedAccount
from infrastructure.simulated_executor import SimulatedExecutor
from domain.ports.fsm.trading_fsm import TradingFSM
from domain.events.market import PriceUpdate
from domain.strategies.statistical_inference.downside_momentum_risk import DownsideMomentumRisk
from domain.signals import Signal
from infrastructure.plotter.graph_generator import GraphGenerator
from infrastructure.plotter.visual_function import VisualFunction
from domain.ports.graph.function_type import FunctionType

def main():
    symbol = "BTC-USD"
    start_date = "2023-01-01"
    end_date = "2024-01-01"
    interval = "1d"
    initial_cash = 10000.0

    print(f"Iniciando Backtest de Downside Momentum Risk para {symbol}...")

    # 1. Obtener Datos Históricos
    data_provider = CachedHistoricalMarketData(cache_dir="data/historical")
    df = data_provider.get_symbol_time_series(symbol, period=None, interval=interval, start=start_date, end=end_date)
    
    if df is None or df.empty:
        print("No se encontraron datos históricos. Revisa la conexión o el rango de fechas.")
        return

    # 2. Inicializar el Entorno de Simulación
    account = SimulatedAccount(initial_cash=initial_cash)
    executor = SimulatedExecutor(account=account)
    # Destiny channel en None para no enviar mensajes reales de Discord durante el backtest
    fsm = TradingFSM(symbol, account, bot_bp=initial_cash, executor=executor, destiny_channel=None)
    executor.register_fsm(fsm)

    # 3. Configurar la Estrategia
    short_alpha = 0.1
    long_alpha = 0.01
    threshold = 2.0
    strategy = DownsideMomentumRisk(
        symbol=symbol, 
        fsm=fsm, 
        short_alpha=short_alpha, 
        long_alpha=long_alpha, 
        threshold=threshold
    )
    fsm.strategies.append(strategy)

    # Historial para graficar
    ewma_s_history = []
    ewma_l_history = []
    
    print(f"Simulando {len(df)} períodos...")

    # Simular compra inicial para tener algo que vender (opcional, para ver la reacción del FSM)
    # strategy.compute_signal(Signal.BUY, 1.0) 

    # 4. Bucle de Simulación
    for timestamp, row in df.iterrows():
        price = float(row["Close"])
        if pd.isna(price):
            # Mantener el valor anterior si no hay datos
            ewma_s_history.append(ewma_s_history[-1] if ewma_s_history else 0)
            ewma_l_history.append(ewma_l_history[-1] if ewma_l_history else 0)
            continue
            
        account.set_current_price(symbol, price)
        executor.set_current_price(symbol, price)
        
        price_update = PriceUpdate(price, symbol)
        
        # Enviamos el evento al FSM y a la estrategia
        fsm.on_event(price_update)
        strategy.update(price_update)
        
        # Almacenamos el estado de las variables para la gráfica
        ewma_s_history.append(strategy.ewma_s)
        ewma_l_history.append(strategy.ewma_l)

    # 5. Generación de Gráficas
    plots_dir = "reports/plots/"
    os.makedirs(plots_dir, exist_ok=True)
    graph_gen = GraphGenerator(plots_dir)
    
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

    # Graficamos EWMA_s y EWMA_l en la misma gráfica para observar los crossovers
    title = f"Downside Momentum Risk (EWMA Crossover) - {symbol}"
    
    print("Generando gráficas...")
    graph_gen.plot_in_R2([f_ewma_s, f_ewma_l], title=title)
    
    print(f"¡Backtest completado! Revisa la carpeta '{plots_dir}' para ver la gráfica de la volatilidad.")

if __name__ == "__main__":
    main()
