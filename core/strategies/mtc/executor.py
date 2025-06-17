from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.risk import RiskCalculator
from core.strategies.base import BaseExecutor
from models import Position


class MajorTrendConfidenceExecutor(BaseExecutor):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        super().__init__(broker, state, config)

    def execute(self, name, direction):

        price = self._price(direction)
        pip_value = self.broker.get_pip_value()

        # TODO fix this have a better SL value!
        sl_distance = 30 * pip_value * 10  # 30pips
        size = self._calculate_volume(sl_distance, self.config.RISK_PER_TRADE)
        stop_loss = self._calculate_stop_loss(price, direction, sl_distance)
        take_profit = self._calculate_take_profit(
            price, direction, self.config.TP_RATIO * sl_distance
        )
        order = self.broker.add_order(
            direction=direction, volume=size, sl=stop_loss, tp=take_profit, comment=name
        )

        if order:
            self.state.position_manager.add_position(
                Position(
                    id=order.order,
                    symbol=self.config.SYMBOL,
                    direction=direction,
                    entry_price=float(order.price),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    size=size,
                    pip_point=pip_value,
                    time_out=0,
                    comment=name,
                )
            )
            return True
        return False
