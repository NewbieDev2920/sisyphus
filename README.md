# SISYPHUS
My name is Sisyphus[ALPHA V0.1], I am the eternal damned, now condemned to trade thy stocks instead of pushing boulders.

## Documentation

### Application Layer
The application layer contains the business logic services.

#### `sisyphus/src/application/account_wallet_service.py`
**Class `AccountWalletService`**
- `__init__(self, account: AccountPort)`: Initializes the service with an account provider.
- `get_summary(self) -> str`: Retrieves a formatted summary of the wallet/account status.

#### `sisyphus/src/application/order_placer_service.py`
**Class `OrderPlacerService`**
- `__init__(self, order_placer: OrderPort)`: Initializes the service with an order placement provider.
- `buy(self, symbol, notional)`: Places a buy order for the specified symbol and notional amount.
- `sell(self, symbol, notional)`: Places a sell order for the specified symbol and notional amount.
- `get_open_orders(self)`: Retrieves a list of currently open orders.

### Domain Layer (Ports)
Defines the interfaces (ports) that the application uses to interact with the infrastructure.

#### `sisyphus/src/domain/ports/account_port.py`
**Class `AccountPort(ABC)`**
Abstract base class defining the interface for account operations.
- `equity`: (Property) Abstract method to get account equity.
- `cash`: (Property) Abstract method to get available cash.
- `pending_transfer`: (Property) Abstract method to get pending transfer funds (in/out).
- `long_market_value`: (Property) Abstract method to get the market value of long positions.
- `summary()`: Abstract method to get a textual summary of the account.

#### `sisyphus/src/domain/ports/order_port.py`
**Class `OrderPort(ABC)`**
Abstract base class defining the interface for order operations.
- `asset_status()`: Abstract method to check the status of an asset.
- `buy()`: Abstract method to place a buy order.
- `sell()`: Abstract method to place a sell order.

#### `sisyphus/src/domain/ports/market_data_port/historical_market_data_port.py`
**Class `HistoricalMarketDataPort(ABC)`**
Abstract interface for fetching historical market data.
- `get_symbol_time_series(symbol, period, interval, start, end) -> pandas.DataFrame`: Abstract method to get time series data for a single symbol.
- `get_multiple_symbols_time_series(symbols, period, interval, start, end) -> pandas.DataFrame`: Abstract method for multiple symbols.
- `price_to_earning_ratio(symbol) -> float`: Abstract method to get P/E ratio.
- `dividends(symbol) -> float`: Abstract method to get dividend information.

#### `sisyphus/src/domain/ports/market_data_port/realtime_market_data_port.py`
**Class `RealtimeMarketDataPort(ABC)`**
Abstract interface for realtime market data.
- `get_asset_price(symbol)`: Abstract method to get current asset price.
- `get_asset_volume(symbol)`: Abstract method to get current asset volume.

### Infrastructure Layer
Implements the interfaces defined in the domain layer, connecting to external services like Alpaca and Yahoo Finance.

#### `sisyphus/src/infrastructure/account/alpaca_account.py`
**Class `AlpacaAccount(AccountPort)`**
Concrete implementation of `AccountPort` using the Alpaca API.
- `__init__(self, trading_client: TradingClient)`: Initializes with an Alpaca `TradingClient`.
- `refresh(self)`: Fetches the latest account data from Alpaca.
- `id`: (Property) Returns account ID.
- `account_number`: (Property) Returns account number.
- `status`: (Property) Returns account status.
- `equity`: (Property) Returns current equity.
- `cash`: (Property) Returns available cash.
- `pending_transfer`: (Property) Returns a dictionary of pending transfers.
- `long_market_value`: (Property) Returns long market value.
- `summary(self) -> str`: Returns a detailed formatted string of the account state (Balance, Changes, Market Value).

#### `sisyphus/src/infrastructure/broker/alpaca_connection.py`
- `SisyphusClient(API_KEY, SECRET)`: Helper function that initializes and returns an Alpaca `TradingClient` using the provided credentials.

#### `sisyphus/src/infrastructure/market_data/HistoricalMarketData.py`
**Class `HistoricalMarketData(HistoricalMarketDataPort)`**
Concrete implementation using `yfinance` to fetch market data.
- `get_symbol_time_series(self, symbol, period, interval, start, end) -> pandas.DataFrame`: Fetches historical data using `yf.Ticker`.
- `get_multiple_symbols_time_series(self, symbols, period, interval, start, end) -> pandas.DataFrame`: Fetches data for list of symbols using `yf.Tickers`.
- `price_to_earning_ratio(self, symbol) -> float`: Returns 'trailingPE' from `yfinance` info.
- `dividends(self, symbol) -> float`: Returns 'dividend' info.

#### `sisyphus/src/infrastructure/order/order_placer.py`
**Class `OrderPlacer(OrderPort)`**
Concrete implementation of `OrderPort` for Alpaca.
- `__init__(self, trading_client)`: Initializes with a trading client and sets a default limit buy price.
- `asset_status(self, symbol) -> str`: Checks if a specific asset is tradable on Alpaca.
- `buy(self, symbol, notional)`: Submits a **Limit Order** to buy the asset at a fixed limit price (default 1000).
- `sell(self, symbol, notional)`: Submits a **Market Order** to sell the asset.
- `get_open_orders(self)`: Fetches up to 100 open orders with `QueryOrderStatus.OPEN`.

### Discord Bot
#### `sisyphus/src/discord_bot/bot.py`
**Class `SisyphusCog(discord.Cog)`**
Handles the Discord slash commands.
- `__init__(self, bot, wallet_service, order_placer_service)`: Injects dependencies.
- `/hello`: Responds with a greeting and bot identity.
- `/wallet`: Displays the current wallet summary from `AccountWalletService`.
- `/buy`: command to place a buy order. Usage: `/buy symbol:AAPL notional:100`.
- `/sell`: command to place a sell order. Usage: `/sell symbol:AAPL notional:100`.
- `/open_orders`: command to list all open orders.

**Class `SisyphusBot(discord.Bot)`**
Custom Discord Bot class.
- `on_ready(self)`: Event handler called when the bot connects; syncs commands and prints debug info.

**Functions**
- `startSisyphus(wallet_service, order_placer_service)`: Entry function that initializes the bot, loads environment variables (GUILD_ID, BOT_TOKEN), and runs the bot.

### Entry Points
#### `sisyphus/src/main.py`
The main application entry script.
1. Loads environment variables from `.env`.
2. Initializes `SisyphusClient` (Alpaca connection).
3. Sets up `AlpacaAccount` and `AccountWalletService`.
4. Sets up `OrderPlacer` and `OrderPlacerService`.
5. Calls `startSisyphus` to run the Discord bot.

#### `sisyphus/src/demo.py`
A demonstration script to test the Alpaca connection independently.
- Loads API keys.
- Initializes `TradingClient`.
- Fetches and prints the open position for 'AAPL'.
