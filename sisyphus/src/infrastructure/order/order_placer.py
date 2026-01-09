from domain.ports.order_port import OrderPort
from alpaca.trading.requests import  LimitOrderRequest, MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

class OrderPlacer(OrderPort):

    def __init__(self, trading_client):
        self.trading_client = trading_client
        self.limit_price_buy = 1000

    #returns if an asset is available for trade.
    def asset_status(self, symbol) -> str:
        try:
           asset =  self.trading_client.get_asset(symbol)
           if asset is not None and asset.tradable:
                return f"Asset {symbol} is available for trading."
           return f"Asset {symbol} is not available for trading."
        except Exception as e:
            return f"Asset {symbol} is not available for trading. {e}"

    #BUY ONLY WITH NOTIONAL
    def buy(self, symbol, notional):
        try:
            order_data = LimitOrderRequest(
            symbol=symbol,
            limit_price = self.limit_price_buy,
            notional = notional,
            side = OrderSide.BUY,
            time_in_force = TimeInForce.DAY
            )

            response = self.trading_client.submit_order(order_data = order_data)
            print("[+]| BUY ORDER SUBMITTED")
            return response
        except Exception as e:
            print(f"[!]| BUY ORDER ERROR {e}")
            return "Something wrong occured with the BUY order creation."

        

        

    def sell(self, symbol, notional):
        try:
            order_data = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )

            response = self.trading_client.submit_order(order_data = order_data)
            print("[-]| SELL ORDER SUBMITTED")
            return response
        except Exception as e:
            print(f"[!]| SELL ORDER ERROR {e}")
            return "Something wrong occured with the SELL order creation."

    def get_open_orders(self):
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            limit=100,
            nested=True
        )
        return self.trading_client.get_orders(request)





        