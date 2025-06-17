from abc import ABC, abstractmethod
from typing import Tuple


class BaseDetector(ABC):
    @abstractmethod
    def detect(self, name) -> Tuple[int, str]: ...


class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, name, direction) -> bool: ...
