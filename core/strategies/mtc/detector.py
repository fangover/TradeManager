import math

import MetaTrader5 as mt5
import numpy as np
from sklearn.linear_model import QuantileRegressor

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.strategies.base import BaseDetector
from models import Candle


class MajorTrendConfidenceDetector(BaseDetector):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config
        self.gamma_threshold = 0.85

    def detect(self):
        timeframe_weights = {
            mt5.TIMEFRAME_D1: 7.0,
            mt5.TIMEFRAME_H4: 4.0,
            mt5.TIMEFRAME_H1: 2.0,
        }

        print("    === Multi-Timeframe Trend Analysis ===")
        daily_bars = self._calculate_realized_vol_bars(mt5.TIMEFRAME_D1)
        h4_bars = self._calculate_realized_vol_bars(mt5.TIMEFRAME_H4)
        h1_bars = self._calculate_realized_vol_bars(mt5.TIMEFRAME_H1)

        daily_trend, daily_trend_conf = self._confirm_trend_with_quantile(
            mt5.TIMEFRAME_D1, daily_bars
        )
        h4_trend, h4_trend_conf = self._confirm_trend_with_quantile(
            mt5.TIMEFRAME_H4, h4_bars
        )
        h1_trend, h1_trend_conf = self._confirm_trend_with_quantile(
            mt5.TIMEFRAME_H1, h1_bars
        )

        if self._in_chop_zone(mt5.TIMEFRAME_H1):
            h1_trend_conf *= 0.4  # Nerf retail timeframe in chop
            print("    CHOP ZONE PENALTY APPLIED - H1 CONFIDENCE REDUCED")

        weighted_trends = [
            daily_trend * daily_trend_conf * timeframe_weights[mt5.TIMEFRAME_D1],
            h4_trend * h4_trend_conf * timeframe_weights[mt5.TIMEFRAME_H4],
            h1_trend * h1_trend_conf * timeframe_weights[mt5.TIMEFRAME_H1],
        ]

        total_weight = sum(timeframe_weights.values())
        composite_trend = sum(weighted_trends) / total_weight
        composite_confidence = abs(composite_trend)

        final_direction = (
            1 if composite_trend > 0 else (-1 if composite_trend < 0 else 0)
        )

        print(
            f"    FINAL TREND: {self.state._trend_to_text(final_direction)} "
            f"| CONFIDENCE: {composite_confidence * 100:.0f}% "
            f"| CAPITAL ALLOC: {self._calculate_position_size(composite_confidence)}%"
        )

        return (final_direction, composite_confidence)

    def _confirm_trend_with_quantile(self, timeframe, bar_count):
        if bar_count < 3:
            return (0, 0.0)

        candles: list[Candle] = self.state.get_candles(timeframe, bar_count)
        if not candles or len(candles) < bar_count:
            return (0, 0.0)

        closes = np.array([candle.close for candle in candles])
        x = np.arange(len(closes)).reshape(-1, 1)

        # Asymmetric trend detection - focuses on downside risks
        qr = QuantileRegressor(quantile=0.33, alpha=1.0, solver="highs")
        qr.fit(x, closes)
        slope = qr.coef_[0]

        bull_factor = np.sum(closes[-3:] > np.median(closes)) / 3.0
        bear_factor = np.sum(closes[-3:] < np.percentile(closes, 40)) / 3.0

        # Modified VWAP calculation for tick volume
        tick_volumes = np.array([candle.volume for candle in candles])
        total_ticks = np.sum(tick_volumes)

        if total_ticks > 0:
            # Tick-volume-weighted price (TVWAP instead of VWAP)
            tvwap = np.sum(tick_volumes * closes) / total_ticks
            price_deviation = (closes[-1] - tvwap) / tvwap if tvwap != 0 else 0
        else:
            # Fallback to median price if no ticks
            tvwap = np.median(closes)
            price_deviation = (closes[-1] - tvwap) / tvwap if tvwap != 0 else 0

        trend = 0
        if slope > 0 and bull_factor > 0.7 and price_deviation > 0:
            trend = 1
        elif slope < 0 and bear_factor > 0.7 and price_deviation < 0:
            trend = -1

        conf = (
            0.5 * min(abs(slope) * 100, 1.0)  # Slope strength
            + 0.3 * max(bull_factor, bear_factor)  # Price factors
            + 0.2 * min(abs(price_deviation) * 10, 1.0)  # Volume-weighted deviation
        )
        conf = min(conf, 1.0)

        tf_text = self.state._timeframe_to_text(timeframe)
        print(
            f"    ({tf_text}) → Trend: {self.state._trend_to_text(trend)} "
            f"| Confidence: {conf*100:.0f}% "
            f"| Slope: {slope:.5f} "
            f"| TVWAP Δ: {price_deviation*100:.2f}% "
            f"| Lookback: {bar_count}"
        )

        return (trend, conf)

    def _calculate_realized_vol_bars(self, timeframe, use_ewma=True, lambda_=0.94):
        # Default volatility targets (can be parameterized externally)
        default_vol_target = {
            mt5.TIMEFRAME_D1: 0.15,
            mt5.TIMEFRAME_H4: 0.25,
            mt5.TIMEFRAME_H1: 0.40,
        }

        # Annualization factors per timeframe
        annualization = {
            mt5.TIMEFRAME_D1: 252,
            mt5.TIMEFRAME_H4: 6 * 252,  # 6 x 4H bars/day
            mt5.TIMEFRAME_H1: 24 * 252,  # 24 x 1H bars/day
        }

        vol_target = default_vol_target.get(timeframe, 0.20)
        ann_factor = annualization.get(timeframe, 252)

        candles = self.state.get_candles(timeframe, 300)
        if not candles or len(candles) < 30:
            return 20

        closes = np.array([c.close for c in candles][-300:])
        log_returns = np.log(closes[1:] / closes[:-1])

        # Use EWMA volatility or simple standard deviation
        if use_ewma:
            weights = np.array([lambda_**i for i in range(len(log_returns))])[::-1]
            weights /= weights.sum()
            mean = np.sum(weights * log_returns)
            variance = np.sum(weights * (log_returns - mean) ** 2)
            realized_vol = np.sqrt(variance) * np.sqrt(ann_factor)
        else:
            realized_vol = np.std(log_returns) * np.sqrt(ann_factor)

        # Inverse vol scaling with square root dampening
        vol_ratio = max(0.5, min(2.0, realized_vol / vol_target))
        base_bars = int(30 / math.sqrt(vol_ratio))

        # Constrain within reasonable bounds
        max_bars = {
            mt5.TIMEFRAME_D1: 90,
            mt5.TIMEFRAME_H4: 60,
            mt5.TIMEFRAME_H1: 90,
        }
        return min(max_bars.get(timeframe, 60), max(10, base_bars))

    def _in_chop_zone(self, timeframe):
        short_atr = self.state.calculate_atr(timeframe, 14, 14)
        long_atr = self.state.calculate_atr(timeframe, 14, 30)
        return short_atr < 0.5 * long_atr if (short_atr and long_atr) else False

    def _calculate_position_size(self, confidence):
        if confidence >= 0.85:
            return 65  # Max conviction sizing
        elif confidence >= 0.70:
            return 40
        elif confidence >= 0.60:
            return 25
        return 0  # No trade below 60% confidence
