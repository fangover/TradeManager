import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import schedule

from core.strategies.base import BaseDetector, BaseExecutor
from core.utilities.event_bus import event_bus
from core.utilities.logger import logger


class Strategy:
    def __init__(
        self,
        name: str,
        detector: BaseDetector,
        executor: BaseExecutor,
        schedule_config: Dict[str, Any] = None,  # type: ignore
        duration_minutes: Optional[int] = None,
    ) -> None:
        self.name = name[:16]  # prevent long text, Important!
        self.detector = detector
        self.executor = executor
        self.bus = event_bus
        self.schedule = schedule_config or {"type": "default"}
        self.duration_minutes = duration_minutes
        self.start_time = datetime.now()

    def should_stop(self) -> bool:
        if self.duration_minutes is None or self.duration_minutes == 0:
            return False
        elapsed = datetime.now() - self.start_time
        return elapsed >= timedelta(minutes=self.duration_minutes)

    def run(self) -> Optional[schedule.CancelJob]:
        start_time = time.time()

        if self.should_stop():
            return schedule.CancelJob  # type: ignore

        direction, reason = self.detector.detect(self.name)
        if direction in (-1, 1):
            try:
                self.executor.execute(self.name, direction)
                execution_time = time.time() - start_time

                logger.info(
                    f"Successfully executed {self.name} strategy | "
                    f"Direction: {'LONG' if direction == 1 else 'SHORT'} | "
                    f"Execution time: {execution_time:.2f}s | "
                    f"Signal reason: {reason}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to execute {self.name} strategy | "
                    f"Direction: {'LONG' if direction == 1 else 'SHORT'} | "
                    f"Error: {str(e)} | "
                    f"Original signal reason: {reason}"
                )
        return None


class StrategyRegistry:
    def __init__(self) -> None:
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
        for strategy in self.strategies:
            strategy.run()

    def run_pending(self) -> None:
        schedule.run_pending()
