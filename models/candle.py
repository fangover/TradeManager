class Candle:
    def __init__(self, timestamp, open, high, low, close, volume, timeframe):
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timeframe = timeframe

    @property
    def body(self):
        return abs(self.close - self.open)

    @property
    def range(self):
        return self.high - self.low

    @property
    def is_bullish(self):
        return self.close > self.open

    @property
    def is_bearish(self):
        return self.close < self.open
