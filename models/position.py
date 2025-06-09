import time


class Position:
    def __init__(
        self,
        id,
        symbol,
        direction,
        entry_price,
        stop_loss,
        take_profit,
        size,
        pip_point,
        time_out,
    ):
        self.id = id
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.size = size
        self.pip_point = pip_point
        self.time_out = time_out
        self.entry_time = time.time()
        self.current_price_ask = entry_price
        self.close_price = None
        self.close_time = None
        self.close_reason = None

    def update_mark_price(self, price):
        self.current_price = price

    def update_sl(self, new_sl):
        self.stop_loss = new_sl

    def update_tp(self, new_tp):
        self.take_profit = new_tp

    @property
    def age(self):
        return time.time() - self.entry_time

    @property
    def unrealized_pnl(self):
        price_diff = self.current_price - self.entry_price
        profit = (price_diff * self.size * self.direction) / self.pip_point
        return round(profit, 2)

    @property
    def unrealized_pnl_pips(self):
        price_diff = self.current_price - self.entry_price
        pips = (price_diff * self.direction) / (self.pip_point * 10)
        return round(pips, 2)

    @property
    def pips_point(self):
        return self.pip_point * 10

    def close(self, reason):
        self.close_price = self.current_price
        self.close_time = time.time()
        self.close_reason = self.close_reason or reason
