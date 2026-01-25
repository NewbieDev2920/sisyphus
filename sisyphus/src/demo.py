import os 
from dotenv import load_dotenv
from infrastructure.market_data.RealtimeMarketData import RealtimeMarketData
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

with Live(layout, console = console, refresh_per_second = 10):

    load_dotenv()

    API_KEY = os.getenv('API_KEY')
    SECRET = os.getenv('SECRET')
    WEBSOCKET_URL = os.getenv('WEBSOCKET_URL')

    conn = RealtimeMarketData(WEBSOCKET_URL, API_KEY, SECRET, console, layout["stream"])
    conn.connect()

    input('PRESS ENTER')

    conn.subscribe('FAKEPACA')

    input()

cmd = Prompt.ask("SISYPHUS")








