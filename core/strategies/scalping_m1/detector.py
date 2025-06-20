from datetime import datetime, timedelta, timezone

import MetaTrader5 as mt5
import numpy as np

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.candle import CandlePlotter
from core.strategies.base import BaseDetector
from core.utilities.logger import logger
from models import Candle


class ScalpingDetector(BaseDetector):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config
        self.prev_rsi = None
        self.gmt_plus_8 = timezone(timedelta(hours=8))

    def detect(self, name):
        if self.broker.has_positions_by_comment(name):
            return 0, f"Existing position found for {name}, skipping new signal"

        candles: list[Candle] = self.state.get_candles(mt5.TIMEFRAME_M1, 30)

        if len(candles) < 30:
            return 0, f"Insufficient candles: {len(candles)}/30, skipping detection"

        closes = np.array([candle.close for candle in candles])

        ema_fast = self._ema(closes, 5)
        ema_slow = self._ema(closes, 13)
        rsi = self._rsi(closes, 14)

        current_close = closes[-1]
        current_rsi = rsi[-1]
        current_fast = ema_fast[-1]
        current_slow = ema_slow[-1]
        prev_fast = ema_fast[-2]
        prev_slow = ema_slow[-2]

        trend_up = current_fast > current_slow and prev_fast <= prev_slow
        trend_down = current_fast < current_slow and prev_fast >= prev_slow

        # Entry conditions
        long_condition = (
            trend_up
            and current_close > current_fast
            and (self.prev_rsi is None or current_rsi < 70)
            and current_rsi > 50
        )

        short_condition = (
            trend_down
            and current_close < current_fast
            and (self.prev_rsi is None or current_rsi > 30)
            and current_rsi < 50
        )

        self.prev_rsi = current_rsi

        signal = 0
        reason = ""
        if long_condition:
            reason = "LONG signal generated. Conditions: trend UP crossover, price above EMA Fast, RSI in [50-70]"
            signal = 1
        elif short_condition:
            reason = "SHORT signal generated. Conditions: trend DOWN crossover, price below EMA Fast, RSI in [30-50]"
            signal = -1

        if signal == 0:
            return signal, "No trading conditions met"

        try:
            tick = self.broker.get_tick()
            if not tick:
                return 0, "Broker tick data unavailable"

            current_time = datetime.now(self.gmt_plus_8)
            date_str = current_time.strftime("%Y-%m-%d_%H-%M-%S")
            direction = "LONG" if signal > 0 else "SHORT"

            plot_title = f"{name} {direction} Signal {date_str}"
            filename = f"{name}_{direction}_{date_str}"
            plotter = CandlePlotter(plot_title)
            plotter.plot_and_save(candles, filename)

            return signal, reason

        except Exception as e:
            return 0, f"Signal processing failed: {str(e)}"

    def _ema(self, prices, period):
        weights = np.exp(np.linspace(0, -1, period))
        weights /= weights.sum()
        ema = np.convolve(prices, weights, mode="full")[: len(prices)]
        ema[:period] = ema[period]
        return ema

    def _rsi(self, prices, period):
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.convolve(gains, np.ones(period) / period, mode="valid")
        avg_loss = np.convolve(losses, np.ones(period) / period, mode="valid")

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return np.concatenate([np.zeros(period), rsi])
