import MetaTrader5 as mt5

from core.candle.candle_manager import CandleManager
from core.infrastructure.brokers.base import BaseBroker
from core.utilities.event_bus import EventBus
from models.position import Position


class TradingState:
    def __init__(self, broker: BaseBroker, bus: EventBus):
        self.broker = broker
        self.bus = bus
        self.candle_manager = CandleManager(broker)
        self.open_positions = {}
        self.position_history = []
        self.account_balance = 10000  # Default starting balance
        self.account_equity = 10000  # Default starting equity
        self.consecutive_losses = 0
        self.session_volatility = 0
        self.halt_trading = False

    def update_account_info(self):
        balance, equity = self.broker.get_account_info()
        self.account_balance = balance
        self.account_equity = equity

    # Candle manager
    def initialize_candles(self):
        self.candle_manager.initialize_all()

    def update_candles(self):
        for timeframe in self.candle_manager.candle_cache.keys():
            self.candle_manager.update_timeframe(timeframe)

    def get_candles(self, timeframe, count=None):
        return self.candle_manager.get_candles(timeframe, count)

    def calculate_atr(self, timeframe, period=14, smoothing_period=None):
        return self.candle_manager.calculate_atr(timeframe, period, smoothing_period)

    # Position manager
    def update_price(self, tick):
        for position in self.open_positions.values():
            position: Position
            position.update_mark_price(
                tick.bid if position.direction == 1 else tick.ask
            )
            position.pip_point = self.broker.get_pip_value()

    def sync_positions(self):
        current_ids = set()
        positions = self.broker.get_positions()
        if positions:
            for pos in positions:
                pos_id = pos.ticket
                current_ids.add(pos_id)

                if pos_id not in self.open_positions:
                    self.add_position(
                        Position(
                            id=pos_id,
                            symbol=pos.symbol,
                            direction=1 if pos.type == 0 else -1,
                            entry_price=pos.price_open,
                            stop_loss=pos.sl,
                            take_profit=pos.tp,
                            size=pos.volume,
                            pip_point=self.broker.get_pip_value(),
                            time_out=0,
                        )
                    )

        existing_ids = set(self.open_positions.keys())
        closed_ids = existing_ids - current_ids
        for pos_id in closed_ids:
            if pos_id in self.open_positions:
                closed_pos: Position = self.open_positions.pop(pos_id)
                closed_pos.close("Closed externally")
                self.bus.publish("LOG_POSITION", closed_pos)
                self.position_history.append(closed_pos)

    def add_position(self, position: Position):
        self.open_positions[position.id] = position
        self.bus.publish("LOG_POSITION", position)

    def close_position(self, position_id, reason):
        if self.broker.close_position(position_id):
            position: Position = self.open_positions.pop(position_id)
            position.close(reason)
            self.bus.publish("LOG_POSITION", position)
            self.position_history.append(position)

            if position.unrealized_pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0

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
