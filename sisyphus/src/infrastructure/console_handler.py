from domain.ports.console_handler_port import ConsoleHandlerPort
import os

class ConsoleHandler(ConsoleHandlerPort):

    def __init__(self, toggle_bot = True):
        self.toggle_bot = toggle_bot
        self.relevant_bot_logs = []
        self.relevant_stream_logs = []

    def toggle(self):
        self.clear_console()
        self.toggle_bot = not self.toggle_bot
        if self.toggle_bot:
            print("STARLOGS-|BOT|***************************************")
            for log in self.relevant_bot_logs:
                print(log)
            
            print("*****************************************************")
        else:
            print("STARLOGS-|STREAM|************************************")
            for log in self.relevant_stream_logs:
                print(log)
            
            print("******************************************************")



    def print_bot(self, text):
        if self.toggle_bot:
            print(text)

    def print_stream(self, text):
        if not self.toggle_bot:
            print(text)

    def star_bot_log(self, text):
        self.relevant_bot_logs.append(text)

    def star_stream_log(self, text):
        self.relevant_stream_logs.append(text)

    def clear_console(self):
        """Clears the console screen."""
        # Check the operating system name
        if os.name == 'nt':
            # For Windows
            _ = os.system('cls')
        else:
            # For macOS and Linux (posix)
            _ = os.system('clear')

# Global instance that can be imported anywhere
_global_console_handler = None

def get_console_handler():
    """Get the global console handler instance"""
    global _global_console_handler
    if _global_console_handler is None:
        _global_console_handler = ConsoleHandler(toggle_bot=True)
    return _global_console_handler

def set_console_handler(handler):
    """Set the global console handler instance"""
    global _global_console_handler
    _global_console_handler = handler
