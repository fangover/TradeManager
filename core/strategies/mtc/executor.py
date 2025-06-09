from config.settings import Settings
from core.risk.calculator import RiskCalculator
from core.state import TradingState
from core.strategies.base import BaseExecutor
from infrastructure.brokers.base import BaseBroker
from models.position import Position


class MajorTrendConfidenceExecutor(BaseExecutor):
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
        )

        stop_loss = price - (direction * sl_distance)
        take_profit = price + (self.config.TP_RATIO * sl_distance * direction)

        order = self.broker.add_order(
            direction=direction, volume=size, sl=stop_loss, tp=take_profit, comment="hi"
        )
        if order:
            self.state.add_position(
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
