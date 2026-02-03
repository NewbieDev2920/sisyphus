from domain.ports.order_port import OrderPort
from alpaca.trading.requests import  MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus

class OrderPlacer(OrderPort):

    def __init__(self, trading_client):
        self.trading_client = trading_client


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
            order_data = MarketOrderRequest(
            symbol=symbol,
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

    def sell(self, symbol : str, notional):
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

    def buy_qty(self, symbol, qty):
        try:
            order_data = MarketOrderRequest(
                symbol = symbol,
                qty = qty,
                side = OrderSide.BUY,
                time_in_force = TimeInForce.DAY
            )

            response = self.trading_client.submit_order(order_data = order_data)
            print("[+]| BUY ORDER SUBMITTED")
            return response
        except Exception as e:
            print(f"[!]| BUY ORDER ERROR {e}")
            return "Something wrong ocurred with the BUY order creation."


    def sell_qty(self, symbol, qty):
        try:
            order_data = MarketOrderRequest(
                symbol = symbol,
                qty = qty,
                side = OrderSide.SELL,
                time_in_force = TimeInForce.DAY
            )

            response = self.trading_client.submit_order(order_data = order_data)
            print("[-]| SELL ORDER SUBMITTED")
            return response
        except Exception as e:
            print(f"[!]| SELL ORDER ERROR {e}")
            return "Something wrong ocurred with the SELL order creation."

    def get_open_orders(self):
        request = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            limit=100,
            nested=True
        )
        return self.trading_client.get_orders(request)





        