import MetaTrader5 as mt5

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.candle import CandlePlotter
from core.infrastructure.risk import RiskCalculator
from core.strategies.base import BaseExecutor
from models import Position


class ScalpingExecutor(BaseExecutor):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        super().__init__(broker, state, config)
        self.trade_duration = 180  # 3 minutes

    def execute(self, name, direction):
        price = self._price(direction)
        atr = self.state.candle_manager.calculate_atr(mt5.TIMEFRAME_M1, 14)
        sl_distance = atr * 1.5
        tp_distance = atr * 3

        stop_loss = self._calculate_stop_loss(price, direction, sl_distance)
        take_profit = self._calculate_take_profit(price, direction, tp_distance)
        size = self._calculate_volume(sl_distance, self.config.RISK_PER_TRADE * 0.5)

        # Execute trade
        order = self.broker.add_order(
            direction=direction,
            volume=size,
            sl=stop_loss,
            tp=take_profit,
            comment=name,
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
                    pip_point=self.broker.get_pip_value(),
                    time_out=self.trade_duration,  # Auto-close after 3 minutes
                    comment=name,
                )
            )
            return True
        return False
