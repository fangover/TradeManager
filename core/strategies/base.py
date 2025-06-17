from abc import ABC, abstractmethod
from typing import Tuple

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers.base import BaseBroker
from core.infrastructure.risk import RiskCalculator


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, name: str) -> Tuple[int, str]: ...


class BaseExecutor(ABC):
    def __init__(self, broker: BaseBroker, state: TradingState, config: Settings):
        self.broker = broker
        self.state = state
        self.config = config

    @abstractmethod
    def execute(self, name: str, direction: int) -> bool: ...

    def _calculate_stop_loss(
        self, price: float, direction: int, sl_distance: float
    ) -> float:
        return RiskCalculator.stop_loss(price, direction, sl_distance)

    def _calculate_take_profit(
        self, price: float, direction: int, tp_distance: float
    ) -> float:
        return RiskCalculator.take_profit(price, direction, tp_distance)

    def _calculate_volume(
        self, sl_distance: float, risk_pct: float | None = None
    ) -> float:

        risk_pct = risk_pct if risk_pct is not None else self.config.RISK_PER_TRADE
        return RiskCalculator.position_size(
            self.state.account_balance,
            sl_distance,
            risk_pct,
            self.broker.get_pip_value(),
            self.config.MIN_LOT_SIZE,
            self.config.MAX_LOT_SIZE,
        )

    def _price(self, direction):
        tick = self.broker.get_tick()
        if not tick:
            return False

        return tick.ask if direction == 1 else tick.bid
