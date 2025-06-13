import MetaTrader5 as mt5

from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.candle import CandleManager
from core.infrastructure.position import PositionManager
from core.utilities.event_bus import EventBus


class TradingState:
    def __init__(self, broker: BaseBroker, bus: EventBus):
        self.broker = broker
        self.bus = bus
        self.candle_manager = CandleManager(broker)
        self.position_manager = PositionManager(broker, bus)
        self.account_balance = 10000  # Default starting balance
        self.account_equity = 10000  # Default starting equity
        self.halt_trading = False

    def update_account_info(self):
        balance, equity = self.broker.get_account_info()
        self.account_balance = balance
        self.account_equity = equity

    def initializ(self):
        self.update_account_info()
        self.candle_manager.initialize_all()

    # Candle manager
    def get_candles(self, timeframe, count=None):
        return self.candle_manager.get_candles(timeframe, count)

    def calculate_atr(self, timeframe, period=14, smoothing_period=None):
        return self.candle_manager.calculate_atr(timeframe, period, smoothing_period)

    def update(self):
        self.update_account_info()
        self.candle_manager.update_candles()
        self.position_manager.sync_positions()

        tick = self.broker.get_tick()
        if tick:
            self.position_manager.update_price(tick)

    # Helper / Converter
    def _trend_to_text(self, trend):
        if trend == 1:
            return "Bullish"
        elif trend == -1:
            return "Bearish"
        else:
            return "Neutral"

    def _timeframe_to_text(self, timeframe):
        mapping = {
            mt5.TIMEFRAME_M1: "M1",
            mt5.TIMEFRAME_M5: "M5",
            mt5.TIMEFRAME_M15: "M15",
            mt5.TIMEFRAME_M30: "M30",
            mt5.TIMEFRAME_H1: "H1",
            mt5.TIMEFRAME_H4: "H4",
            mt5.TIMEFRAME_D1: "D1",
        }
        return mapping.get(timeframe, f"Unknown({timeframe})")
