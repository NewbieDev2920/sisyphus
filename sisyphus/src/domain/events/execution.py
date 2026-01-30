from domain.events.event import Event


class OrderSent(Event):
    def __init__(self, order_id):
        self.order_id = order_id

class OrderFilled(Event):
    def __init__(self, order_id):
        self.order_id = order_id

class OrderRejected(Event):
    def __init__(self, order_id):
        self.order_id = order_id