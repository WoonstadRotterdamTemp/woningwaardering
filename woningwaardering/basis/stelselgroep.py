from abc import ABC
from datetime import datetime


class StelselGroep(ABC):
    def __init__(self, peildatum: str, datamodel, datum_regel_mapping) -> None:
        self.peildatum = datetime.strptime(peildatum, "%Y-%m-%d").date()
        self.datum_regel_mapping = datum_regel_mapping
        self.datamodel = datamodel
        self.punten = self.bereken(datamodel)

    def geldige_regels(self) -> list:
        for datum, regel in sorted(self.datum_regel_mapping.items(), reverse=True):
            if self.peildatum >= datetime.strptime(datum, "%Y-%m-%d").date():
                return regel
        return []

    def bereken(self, datamodel: dict) -> int:
        regels = self.geldige_regels()
        return sum(regel.bereken(datamodel) for regel in regels)

    def __str__(self) -> str:
        return f"StelselGroep: {self.__class__.__name__}, datum: {self.peildatum}, punten: {self.punten}, datamodel: {self.datamodel}"
