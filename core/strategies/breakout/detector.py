import MetaTrader5 as mt5

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.strategies.base import BaseDetector
from models.candle import Candle


class BreakoutDetector(BaseDetector):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config

    def detect(self):
        volatility = self.state.candle_manager.calculate_volatility(mt5.TIMEFRAME_D1)
        threshold = self.config.BREAKOUT_THRESHOLD + (volatility * 0.2)

        candles: list[Candle] = self.state.get_candles(mt5.TIMEFRAME_D1, 5)
        if len(candles) < 2:
            return None

        prev_candle = candles[-2]
        current_candle = candles[-1]

        resistance = max(prev_candle.high, current_candle.open)
        support = min(prev_candle.low, current_candle.open)

        tick = self.broker.get_tick()
        if not tick:
            return None

        if tick.bid > resistance + (threshold * (resistance - support)):
            return 1
        elif tick.ask < support - (threshold * (resistance - support)):
            return -1
        return 0
