from abc import ABC, abstractmethod


class BaseDetector(ABC):
    @abstractmethod
    def detect(self) -> int: ...


class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, direction) -> bool: ...
