from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


import pandas as pd


class Regel(ABC):
    def __init__(self, datamodel: dict) -> None:
        self.datamodel = datamodel

    def __call__(self) -> Any:
        return Regel.bereken(self.datamodel)

    @staticmethod
    @abstractmethod
    def bereken(datamodel: dict) -> float:
        pass


class StelselGroep(ABC):
    def __init__(
        self, peildatum: str, datamodel: dict, datum_regel_mapping: dict
    ) -> None:
        self.peildatum = datetime.strptime(peildatum, "%Y-%m-%d").date()
        self.datum_regel_mapping = datum_regel_mapping
        self.datamodel = datamodel
        self.punten = self.bereken(datamodel)

    def geldige_regels(self) -> list:
        for datum, regels in sorted(self.datum_regel_mapping.items(), reverse=True):
            if self.peildatum >= datetime.strptime(datum, "%Y-%m-%d").date():
                return regels
        return []

    def bereken(self, datamodel: dict) -> int:
        regels = self.geldige_regels()
        return sum(regel.bereken(datamodel) for regel in regels)

    def __str__(self) -> str:
        return f"StelselGroep: {self.__class__.__name__}, datum: {self.peildatum}, punten: {self.punten}, datamodel: {self.datamodel}"


class EnergiePrestatie(Regel):
    print("LOADING ref data")
    REF_DATA = pd.read_csv("./referentie_data/oppervlakte.csv")

    def bereken(datamodel: dict) -> int:
        print(EnergiePrestatie.REF_DATA)
        return 10


class EenPuntPerM2Oppervlakte(Regel):
    def bereken(datamodel: dict) -> int:
        return int(datamodel.get("oppervlakte", 0))


class TweePuntenPerM2Oppervlakte(Regel):
    def bereken(datamodel: dict) -> int:
        return int(datamodel.get("oppervlakte", 0) * 2)


class OppervlakteVanVertrekken(StelselGroep):
    DATUM_REGEL_MAPPING = {
        "2024-01-01": [TweePuntenPerM2Oppervlakte, EnergiePrestatie],
        "2000-01-01": [EenPuntPerM2Oppervlakte],
    }

    def __init__(self, peildatum: str, datamodel: dict) -> None:
        super().__init__(peildatum, datamodel, self.DATUM_REGEL_MAPPING)


datamodel = {"oppervlakte": 100, "label": "A"}


op = OppervlakteVanVertrekken("2025-01-01", datamodel)
print(op)
op = OppervlakteVanVertrekken("2025-01-01", datamodel)
print(op)
