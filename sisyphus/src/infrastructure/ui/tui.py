from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
import sys
from io import StringIO

class TUIStdout:
    def __init__(self, tui):
        self.tui = tui
        self.original_stdout = sys.stdout

    def write(self, message):
        if message.strip():  # Avoid empty newlines creating gaps
            self.tui.log(message.strip())
        # Optional: still write to original stdout if needed for debugging, 
        # but usually we want to intercept it completely.

    def flush(self):
        pass

class SisyphusTUI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.layout.split_row(
            Layout(name="stream", ratio=1),
            Layout(name="sisyphus_bot", ratio=1)
        )
        self.logs = []
        self.MAX_LOGS = 20
        self.live = None
        self.original_stdout = None

        # Initialize empty panels
        self.update_stream("Waiting for market data...")
        self.update_logs()

    def update_stream(self, content):
        # Truncate very long content to prevent layout issues
        content_str = str(content)
        if len(content_str) > 2000:
            content_str = content_str[-2000:]  # Keep last 2000 chars
        
        panel = Panel(
            Text(content_str, overflow="fold"),
            title="ALPACA STREAM",
            border_style="cyan"
        )
        self.layout["stream"].update(panel)

    def log(self, message):
        self.logs.append(message)
        if len(self.logs) > self.MAX_LOGS:
            self.logs.pop(0)
        self.update_logs()

    def update_logs(self):
        content = "\n".join(self.logs)
        panel = Panel(
            Text(content, overflow="fold"),
            title="SISYPHUS LOGS",
            border_style="green"
        )
        self.layout["sisyphus_bot"].update(panel)

    def __enter__(self):
        # Create and start the Live display using its context manager
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.live.__enter__()
        
        # Redirect stdout
        self.original_stdout = sys.stdout
        sys.stdout = TUIStdout(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore stdout
        sys.stdout = self.original_stdout
        
        # Stop the Live display
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)
        
        return False
