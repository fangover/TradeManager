import time
from collections import deque

import MetaTrader5 as mt5
import numpy as np

from core.infrastructure.brokers.base import BaseBroker
from models.candle import Candle


class CandleManager:
    def __init__(self, broker: BaseBroker):
        self.broker = broker

        # Total estimated memory: ~1.3 MB
        self.candle_cache = {
            mt5.TIMEFRAME_M1: deque(maxlen=10080),  # 1 week of 1-minute candles
            mt5.TIMEFRAME_M5: deque(maxlen=2016),  # 1 week of 5-minute candles
            mt5.TIMEFRAME_M15: deque(maxlen=672),  # 1 week of 15-minute candles
            mt5.TIMEFRAME_M30: deque(maxlen=336),  # 1 week of 30-minute candles
            mt5.TIMEFRAME_H1: deque(maxlen=168),  # 1 week of 1-hour candles
            mt5.TIMEFRAME_H4: deque(maxlen=84),  # 2 weeks of 4-hour candles
            mt5.TIMEFRAME_D1: deque(maxlen=90),  # 3 months of daily candles
        }

        self.timeframe_seconds = {
            mt5.TIMEFRAME_M1: 60,
            mt5.TIMEFRAME_M5: 300,
            mt5.TIMEFRAME_M15: 900,
            mt5.TIMEFRAME_M30: 1800,
            mt5.TIMEFRAME_H1: 3600,
            mt5.TIMEFRAME_H4: 14400,
            mt5.TIMEFRAME_D1: 86400,
        }
        self.timeframe_text = {
            mt5.TIMEFRAME_M1: "M1",
            mt5.TIMEFRAME_M5: "M5",
            mt5.TIMEFRAME_M15: "M15",
            mt5.TIMEFRAME_M30: "M30",
            mt5.TIMEFRAME_H1: "H1",
            mt5.TIMEFRAME_H4: "H4",
            mt5.TIMEFRAME_D1: "D1",
        }

    def initialize_timeframe(self, timeframe):
        """Initialize candle cache for a specific timeframe"""
        if len(self.candle_cache[timeframe]) == 0:
            start = time.time()
            candles = self.broker.get_candles(
                timeframe, self.candle_cache[timeframe].maxlen or 0
            )
            if candles is not None:
                for c in candles:
                    self.add_candle(
                        Candle(
                            timestamp=c["time"],
                            open=c["open"],
                            high=c["high"],
                            low=c["low"],
                            close=c["close"],
                            volume=c["tick_volume"],
                            timeframe=timeframe,
                        )
                    )
            print(
                f"Initialized {self.timeframe_text.get(timeframe, timeframe)} "
                f"with {len(candles)} candles "  # type: ignore
                f"in {time.time() - start:.2f}s"
            )

    def initialize_all(self):
        """Initialize all timeframes"""
        for timeframe in self.candle_cache.keys():
            self.initialize_timeframe(timeframe)

    def add_candle(self, candle: Candle):
        """Add a new candle to the appropriate timeframe cache"""
        self.candle_cache[candle.timeframe].append(candle)

    def get_candles(self, timeframe, count=None):
        """Get candles for a specific timeframe"""
        candles = self.candle_cache.get(timeframe, deque())
        candles_list = list(candles)

        if count is None or count >= len(candles_list):
            return candles_list

        return candles_list[-count:]

    def update_candles(self):
        for timeframe in self.candle_cache.keys():
            self.update_timeframe(timeframe)

    def update_timeframe(self, timeframe):
        """Update candle cache for a specific timeframe"""
        latest = self.broker.get_candles(timeframe, 1)
        if not latest:
            return

        c = latest[0]
        new_candle = Candle(
            timestamp=c["time"],
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["tick_volume"],
            timeframe=timeframe,
        )

        # Initialize if empty
        if not self.candle_cache[timeframe]:
            self.initialize_timeframe(timeframe)
            return

        last_candle = self.candle_cache[timeframe][-1]

        # New candle detected
        if new_candle.timestamp != last_candle.timestamp:
            self.add_candle(new_candle)
            # Handle gaps (especially important for daily candles)
            gap = new_candle.timestamp - last_candle.timestamp
            timeframe_sec = self.timeframe_seconds.get(timeframe, 60)
            if gap > timeframe_sec * 1.5:
                self._fill_gap(timeframe, last_candle, new_candle)

        # Update current candle
        else:
            last_candle.high = max(last_candle.high, new_candle.high)
            last_candle.low = min(last_candle.low, new_candle.low)
            last_candle.close = new_candle.close
            last_candle.volume += new_candle.volume

    def _fill_gap(self, timeframe, last_candle, new_candle):
        """Fill missing candles between last candle and new candle"""
        gap_duration = new_candle.timestamp - last_candle.timestamp
        timeframe_sec = self.timeframe_seconds.get(timeframe, 60)
        missing_count = int(gap_duration // timeframe_sec) - 1

        for i in range(1, missing_count + 1):
            gap_time = last_candle.timestamp + i * timeframe_sec
            self.candle_cache[timeframe].append(
                Candle(
                    timestamp=gap_time,
                    open=last_candle.close,
                    high=last_candle.close,
                    low=last_candle.close,
                    close=last_candle.close,
                    volume=0,
                    timeframe=timeframe,
                )
            )

    def calculate_atr(
        self, timeframe: int, lookback_period: int, smoothing_period=None
    ):
        candles = self.get_candles(timeframe, lookback_period + 1)
        if not candles or len(candles) < lookback_period:
            return 0.0

        true_ranges = []
        for i in range(1, len(candles)):
            high, low, prev_close = (
                candles[i].high,
                candles[i].low,
                candles[i - 1].close,
            )
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            true_ranges.append(tr)

        if smoothing_period:
            weights = np.exp(np.linspace(0, -1, smoothing_period))
            weights /= weights.sum()
            atr = np.convolve(true_ranges[-smoothing_period:], weights, mode="valid")[0]
        else:
            # Simple moving average
            atr = np.mean(true_ranges[-lookback_period:])

        recent_vol = np.std(
            [c.close for c in candles[-20:]]
        )  # 20-period close volatility
        long_term_vol = np.std([c.close for c in candles])
        volatility_ratio = recent_vol / (long_term_vol + 1e-10)

        return atr * (0.5 + 0.5 * volatility_ratio)

    def calculate_volatility(self, timeframe):
        candles = list(self.candle_cache[timeframe])
        if len(candles) < 2:
            return 0

        returns = np.log([c.close / c.open for c in candles])
        return np.std(returns) * np.sqrt(len(candles))
