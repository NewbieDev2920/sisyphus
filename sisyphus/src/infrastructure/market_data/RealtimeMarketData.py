import websocket
from domain.ports.market_data_port.realtime_market_data_port import RealtimeMarketDataPort
import websocket 
import json 
import threading
from rich.panel import Panel
from rich.text import Text


class RealtimeMarketData(RealtimeMarketDataPort):
    #FAKE SYMBOL FOR TESTING : 'FAKEPACA'
    #REFACTORIZAR API_KEY Y SECRET PARA MANTENER SINGLE RESPONSABILITY PRINCIPLE.
    #30 SYMBOLS STREAM LIMIT.
    #REVISAR RENDIMIENTO AL USAR PYTHON LIST, POSIBLEMENTE CAMBIAR A NUMPY.NDARRAY.


    """

    REFACTORIZA TODA ESTA MIERDA.

    """
    def __init__(self, SOCKET_URL, API_KEY, SECRET, console_layout, layout):
        self.console_layout = console_layout
        self.layout = layout
        self.API_KEY = API_KEY
        self.SECRET= SECRET
        self.SOCKET_URL = SOCKET_URL
        self.official_registered_symbols = []
        self.registered_symbols = self.official_registered_symbols.copy()
        self.ws = websocket.WebSocketApp(self.SOCKET_URL, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)

        self.is_connected = False
        self.is_auth_req_sent = False
        self.last_quotes = []
        self.LAST_QUOTES_MAX_LENGTH = 37
        self.authenticated_event = threading.Event()
        self.logs = []
        self.MAX_LOGS = 12

    def _display(self, text):
        self.logs.append(text)
        if len(self.logs) > self.MAX_LOGS:
            self.logs.pop(0)

        content = "\n".join(self.logs)

        panel = Panel(
            Text(content, overflow="fold"),
            title="ALPACA STREAM",
            border_style="cyan"
        )
        self.layout.update(panel)

    #Revisar teoria de threads y daemon.
    def connect(self):
        self._display(f"SISYPHUS> connect to ALPACA ({self.SOCKET_URL})")

        thread = threading.Thread(
            target= self.ws.run_forever,
            daemon = True
        )
        thread.start()

    def authenticate(self):
        self._display("SISYPHYS> authenticate")

        req = {"action": "auth", "key":self.API_KEY, "secret": self.SECRET}
        self.ws.send(json.dumps(req))
        self.is_auth_req_sent = True

    def subscribe(self, symbol):
        self._display(f"SISYPHUS> subscribe the following symbol: {symbol}")

        req = {"action": "subscribe", "quotes": [symbol]}
        self._send(req)
        self.registered_symbols.append(symbol)

    def subscribe_all_official_registered_symbols(self):
        self._display(f"ALPACA> subscribe the following official symbols: {self.official_registered_symbols}")

        req = {"action": "subscribe", "quotes": self.official_registered_symbols}
        self._send(req)
    
    def unsubscribe(self, symbol):
        self._display(f"SISYPHUS> unsubscribe the following symbol: {symbol}")

        req = {"action": "unsubscribe", "quotes": [symbol]}
        self._send(req)
        self.registered_symbols.remove(symbol)

    #NOT COMPLETED, DO NOT USE IT. POSSIBLE RATELIMIT EXCESS.
    def unsubscribe_all(self):
        self._display(f"SISYPHUS> unsubscribe the following symbols: {self.registered_symbols}")

        for symbol in self.registered_symbols:
            self.unsubscribe(symbol)
    
    def on_open(self, ws):
        self._display("SYSYPHUS> ALPACA_MARKET_API stream connection opened")

        self.authenticate()
        self.is_connected = True
    
    def on_message(self, ws, message):
        self._display(f"ALPACA> {message}")

        msg = json.loads(message)

        for m in msg:
            t = m.get("T")
            if t == "success":
                status = m.get("msg")
                self._display(f"ALPACA>  {status}")

                if status == "authenticated":
                    self.authenticated_event.set()
            elif t == "q":
                self.last_quotes.append(m)
                if len(self.last_quotes) > self.LAST_QUOTES_MAX_LENGTH:
                    self.last_quotes.pop(0) 

    def get_last_quotes(self):
        return self.last_quotes[self.LAST_QUOTES_MAX_LENGTH - 1]


    def on_error(self, ws, error):
        self._display(f"SYSYPHUS> An error occurred {error}")


    def on_close(self, ws):
        self._display("SYSYPHUS> ALPACA_MARKET_API stream connection closed")


    def _send(self,payload):
        if not self.authenticated_event.is_set():
            raise RuntimeError("WEBSOCKET_STREAM IS NOT AUTHENTICATED.")
        self.ws.send(json.dumps(payload))


