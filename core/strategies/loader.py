from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import schedule

from core.strategies.base import BaseDetector, BaseExecutor
from core.utilities.logger import logger
from infrastructure.event_bus import event_bus


class Strategy:
    """A trading strategy combining detection and execution logic."""

    def __init__(
        self,
        name: str,
        detector: BaseDetector,
        executor: BaseExecutor,
        schedule_config: Dict[str, Any] = None,  # type: ignore
        duration_minutes: Optional[int] = None,
    ) -> None:
        """Initialize the strategy.

        Args:
            name: Strategy identifier
            detector: Detection logic component
            executor: Execution logic component
            schedule_config: Scheduling configuration
            duration_minutes: Optional runtime limit in minutes
        """
        self.name = name
        self.detector = detector
        self.executor = executor
        self.bus = event_bus
        self.schedule = schedule_config or {"type": "default"}
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()

    def should_stop(self) -> bool:
        """Check if strategy should stop based on duration limit."""
        if self.duration_minutes is None or self.duration_minutes == 0:
            return False
        elapsed = datetime.now() - self.start_time
        return elapsed >= timedelta(minutes=self.duration_minutes)

    def run(self) -> Optional[schedule.CancelJob]:
        """Execute the strategy's detection and execution logic."""
        if self.should_stop():
            return schedule.CancelJob  # type: ignore

        logger.info(f"Detecting {self.name} strategy")
        direction = self.detector.detect()
        if direction in (-1, 1):
            logger.info(f"Executing {self.name} strategy")
            self.executor.execute(direction)
        return None


class StrategyRegistry:
    """Manages registration and scheduling of trading strategies."""

    def __init__(self) -> None:
        """Initialize the registry."""
        self.strategies = []
        self.default_strategy = None

    def load(
        self,
        name: str,
        detector: BaseDetector,
        executor: BaseExecutor,
        schedule_config: Dict[str, Any] = None,  # type: ignore
        duration_minutes: Optional[int] = None,
    ) -> "StrategyRegistry":
        """Load and schedule a strategy.

        Args:
            name: Strategy identifier
            detector: Detection logic component
            executor: Execution logic component
            schedule_config: Scheduling configuration
            duration_minutes: Optional runtime limit in minutes

        Returns:
            StrategyRegistry: self for method chaining
        """
        strategy = Strategy(name, detector, executor, schedule_config, duration_minutes)
        self.strategies.append(strategy)

        if schedule_config is None or schedule_config.get("type") == "default":
            if self.default_strategy is None:
                self.default_strategy = strategy
            schedule.every(10).seconds.do(strategy.run)
        else:
            self._schedule_strategy(strategy)

        return self

    def _schedule_strategy(self, strategy: Strategy) -> None:
        """Internal method to schedule a strategy.

        Args:
            strategy: Strategy instance to schedule
        """
        cfg = strategy.schedule

        if cfg["type"] == "interval":
            schedule.every(cfg["seconds"]).seconds.do(strategy.run)
        elif cfg["type"] == "daily":
            schedule.every().day.at(cfg["at"]).do(strategy.run)
        elif cfg["type"] == "hourly":
            at_time = cfg.get("at", ":00")
            if not at_time.startswith(":"):
                at_time = f":{at_time}"
            schedule.every().hour.at(at_time).do(strategy.run)

    def run_all(self) -> None:
        """Run all registered strategies immediately."""
        for strategy in self.strategies:
            strategy.run()

    def run_pending(self) -> None:
        """Run all pending scheduled tasks."""
        schedule.run_pending()
