import time

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers import BrokerFactory
from core.infrastructure.position import PositionLogger
from core.infrastructure.risk import RiskManager
from core.strategies.loader import StrategyRegistry
from core.strategies.mtc import (
    MajorTrendConfidenceDetector,
    MajorTrendConfidenceExecutor,
)
from core.strategies.scalping_m1 import ScalpingDetector, ScalpingExecutor
from core.utilities.event_bus import EventBus
from core.utilities.logger import logger


class TradeApp:
    def __init__(self, config: Settings):
        self.broker = BrokerFactory.create(config)
        self.bus = EventBus()

        self.state = TradingState(self.broker, self.bus)
        self.position_logger = PositionLogger()
        self.bus.subscribe("LOG_POSITION", self.position_logger.log_position)

        self.state.initialize()

        # Load in strategies
        self.strategies = StrategyRegistry()
        self.strategies.load(
            "Major Trend Conf",
            MajorTrendConfidenceDetector(self.broker, self.state, config),
            MajorTrendConfidenceExecutor(self.broker, self.state, config),
            schedule_config={"type": "hourly", "at": ":00"},
            duration_minutes=15,
        )
        self.strategies.load(
            "M1 Scalping",
            ScalpingDetector(self.broker, self.state, config),
            ScalpingExecutor(self.broker, self.state, config),
            schedule_config={"type": "interval", "seconds": 10},
            duration_minutes=0,  # Run continuously
        )

        self.strategies.load(
            "M1 Scalping RM",
            ScalpingDetector(self.broker, self.state, config),
            ScalpingExecutor(self.broker, self.state, config),
            schedule_config={"type": "interval", "seconds": 10},
            duration_minutes=0,  # Run continuously
        )

        self.risk = RiskManager(
            self.broker, self.state, config, self.bus, ["M1 Scalping"]
        )

        # Event bindings
        self.bus.subscribe("RISK_VIOLATION", self.on_risk_violation)

        self.running = True

    def on_risk_violation(self, msg):
        logger.critical(f"RISK: {msg}")
        # self.state.halt_trading = True : Not completed

    def run(self):
        logger.info("📈 TradeApp Started")

        while self.running and not self.state.halt_trading:
            try:
                self.state.update()
                self.strategies.run_pending()
                self.risk.evaluate()
                time.sleep(1)
            except Exception as e:
                logger.exception(f"Loop Error: {e}")
            finally:
                time.sleep(0.1)

    def shutdown(self):
        logger.info("TradeApp Shutdown Complete")
