from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.risk import RiskCalculator
from core.strategies.base import BaseExecutor
from models import Position


class BreakoutExecutor(BaseExecutor):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config

    def execute(self, direction):
        tick = self.broker.get_tick()
        if not tick:
            return False

        price = tick.ask if direction == 1 else tick.bid
        sl_distance = price * 30
        pip_value = self.broker.get_pip_value()

        size = RiskCalculator.position_size(
            self.state.account_balance,
            sl_distance,
            self.config.RISK_PER_TRADE,
            pip_value,
            self.config.MIN_LOT_SIZE,
            self.config.MAX_LOT_SIZE,
        )

        stop_loss = price - (direction * sl_distance)
        take_profit = price + (self.config.TP_RATIO * sl_distance * direction)

        order = self.broker.add_order(
            direction=direction, volume=size, sl=stop_loss, tp=take_profit, comment="hi"
        )
        if order:
            self.state.position_manager.add_position(
                Position(
                    id=order.ticket,
                    symbol=self.config.SYMBOL,
                    direction=direction,
                    entry_price=order.price,
                    stop_loss=order.sl,
                    take_profit=order.tp,
                    size=order.volume,
                    pip_point=self.broker.get_pip_value(),
                    time_out=0,
                )
            )
            return True
        return False
