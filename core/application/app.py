import time

from config.settings import Settings
from core.application.state import TradingState
from core.infrastructure.brokers import BrokerFactory
from core.infrastructure.candle.candle_plotter import CandlePlotter
from core.infrastructure.position.position_logger import PositionLogger
from core.infrastructure.risk.manager import RiskManager
from core.strategies.breakout.detector import BreakoutDetector
from core.strategies.breakout.executor import BreakoutExecutor
from core.strategies.loader import StrategyRegistry
from core.strategies.mtc.detector import MajorTrendConfidenceDetector
from core.strategies.mtc.executor import MajorTrendConfidenceExecutor
from core.utilities.event_bus import EventBus
from core.utilities.logger import logger


class TradeApp:
    def __init__(self, config: Settings):
        self.broker = BrokerFactory.create(config)
        self.bus = EventBus()

        self.state = TradingState(self.broker, self.bus)
        self.position_logger = PositionLogger()
        self.bus.subscribe("LOG_POSITION", self.position_logger.log_position)

        self.state.initializ()

        self.risk = RiskManager(self.broker, self.state, config, self.bus)

        # Load in strategies
        self.strategies = StrategyRegistry()
        self.strategies.load(
            "Breakout",
            BreakoutDetector(self.broker, self.state, config),
            BreakoutExecutor(self.broker, self.state, config),
            schedule_config={"type": "hourly", "at": ":30"},
            duration_minutes=1,
        )
        self.strategies.load(
            "Major Trend Confidence",
            MajorTrendConfidenceDetector(self.broker, self.state, config),
            MajorTrendConfidenceExecutor(self.broker, self.state, config),
            schedule_config={"type": "hourly", "at": ":00"},
            duration_minutes=10,
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
