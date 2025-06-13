import MetaTrader5 as mt5

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.risk import RiskCalculator
from core.strategies.base import BaseExecutor
from models import Position


class ScalpingExecutor(BaseExecutor):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config
        self.max_trades = 3  # Max simultaneous trades
        self.trade_duration = 180  # 3 minutes

    def execute(self, direction):
        if len(self.state.position_manager.open_positions) >= self.max_trades:
            return False

        tick = self.broker.get_tick()
        if not tick:
            return False

        price = tick.ask if direction == 1 else tick.bid

        atr = self.state.candle_manager.calculate_atr(mt5.TIMEFRAME_M1, 14)
        pip_value = self.broker.get_pip_value()

        sl_distance = atr * 1.5
        tp_distance = atr * 3

        stop_loss = price - (direction * sl_distance)
        take_profit = price + (direction * tp_distance)

        size = RiskCalculator.position_size(
            self.state.account_balance,
            sl_distance,
            self.config.RISK_PER_TRADE * 0.5,  # Half normal risk
            pip_value * 10,
            self.config.MIN_LOT_SIZE,
            self.config.MAX_LOT_SIZE,
        )

        # Execute trade
        order = self.broker.add_order(
            direction=direction,
            volume=size,
            sl=stop_loss,
            tp=take_profit,
            comment="SCALP",
        )

        if order:
            self.state.position_manager.add_position(
                Position(
                    id=order.ticket,
                    symbol=self.config.SYMBOL,
                    direction=direction,
                    entry_price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    size=size,
                    pip_point=pip_value,
                    time_out=self.trade_duration,  # Auto-close after 3 minutes
                )
            )
            return True
        return False
