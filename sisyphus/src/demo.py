import os 
from dotenv import load_dotenv
from infrastructure.market_data.RealtimeMarketData import RealtimeMarketData
from infrastructure.reporters.demo_reporter import DemoReporter
from domain.strategies.monotonic_increasing import MonotonicIncreasing
from rich import print
from rich.layout import Layout

from rich.console import Console
from rich.live import Live

from rich.prompt import Prompt

console = Console()
layout = Layout()
layout.split_row(
    Layout(name="stream"),
    Layout(name="commands")
)
demo_reporter = DemoReporter()
with Live(layout, console = console, refresh_per_second = 10):

    load_dotenv()

    API_KEY = os.getenv('API_KEY')
    SECRET = os.getenv('SECRET')
    WEBSOCKET_URL = os.getenv('WEBSOCKET_URL')

    conn = RealtimeMarketData(WEBSOCKET_URL, API_KEY, SECRET, console, layout["stream"])
    conn.connect()

    input('PRESS ENTER')
    
    conn.append_reporter(demo_reporter)
    #MUST SUBSCRIBE BEFORE ADDING STRATEGIES.
    conn.subscribe('AMD')
    strategy1 = MonotonicIncreasing("AMD")
    strategy1.realtimemarketdata = conn
    conn.append_observer(strategy1)
    

    input()
    

cmd = Prompt.ask("SISYPHUS")
print(demo_reporter.journal())
print("OUTPUT DE STRATEGY1: ")
print(strategy1.output)








