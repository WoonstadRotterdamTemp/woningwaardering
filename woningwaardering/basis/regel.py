from abc import ABC, abstractmethod
from typing import Any


class Regel(ABC):
    def __init__(self, datamodel: dict) -> None:
        self.datamodel = datamodel

    def __call__(self) -> Any:
        return Regel.bereken(self.datamodel)

    @staticmethod
    @abstractmethod
    def bereken(datamodel: dict) -> float:
        pass
