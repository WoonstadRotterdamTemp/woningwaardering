from abc import ABC
from datetime import date
from typing import Type

from loguru import logger

from woningwaardering.stelsels.config import Stelselconfig
from .utils import import_class, is_geldig
from .stelselgroepversie import Stelselgroepversie
from woningwaardering.vera.bvg.generated import (
    EenhedenEenheid,
    WoningwaarderingResultatenWoningwaarderingGroep,
    WoningwaarderingResultatenWoningwaarderingResultaat,
)
from woningwaardering.vera.referentiedata import (
    Woningwaarderingstelsel,
    Woningwaarderingstelselgroep,
)


class _StelselgroepABC(ABC):
    def __init__(
        self,
        stelsel: Woningwaarderingstelsel,
        stelselgroep: Woningwaarderingstelselgroep,
        peildatum: date,
    ) -> None:
        super().__init__()
        self.stelsel = stelsel
        self.stelselgroep = stelselgroep
        self.geldig_versie = self.select_stelselgroepversie(
            stelsel, stelselgroep, peildatum
        )

    @staticmethod
    def select_stelselgroepversie(
        stelsel: Woningwaarderingstelsel,
        stelselgroep: Woningwaarderingstelselgroep,
        peildatum: date = date.today(),
        config: Stelselconfig | None = None,
    ) -> Stelselgroepversie:
        """Selecteert de geldige stelselgroepversie op basis van de opgegeven peildatum, stelsel en stelselgroep.

        Args:
            stelsel (Woningwaarderingstelsel): Het stelsel waartoe de stelselgroep behoort.
            stelselgroep (Woningwaarderingstelselgroep): De naam van de stelselgroep.
            peildatum (date): De peildatum voor de waardering.
            config (Stelselconfig| None, optional): De configuratie. Defaults to None.

        Returns:
            Stelselgroepversie: De geldige stelselgroepversie.

        Raises:
            ValueError: Als er geen geldige stelselgroepen zijn gevonden met de opgegeven peildatum.
            ValueError: Als er meerdere geldige stelselgroepen zijn gevonden met de opgegeven peildatum.
        """
        if not config:
            config = Stelselconfig.load(stelsel=stelsel)

        stelselgroep_config = config.stelselgroepen[stelselgroep.name]

        geldige_stelselgroep_versie_configs = [
            versie
            for versie in stelselgroep_config.versies
            if is_geldig(versie.begindatum, versie.einddatum, peildatum)
        ]

        if not geldige_stelselgroep_versie_configs:
            raise NotImplementedError(
                f"geen geldige stelselgroep configuratie gevonden voor stelsel {stelsel} met peildatum {peildatum}"
            )

        if len(geldige_stelselgroep_versie_configs) > 1:
            raise ValueError(
                f"meerdere geldige stelselgroep configuraties gevonden voor {stelsel.value.naam} met peildatum {peildatum}: {geldige_stelselgroep_versie_configs}"
            )

        logger.debug(
            f"{stelsel.value.naam}: stelselgroep '{stelselgroep}' is geldig op peildatum {peildatum}."
        )
        logger.debug(f"{stelsel.value.naam}: versies: {stelselgroep_config.versies}")

        geldige_stelselgroep_versie_config = geldige_stelselgroep_versie_configs[0]

        stelselgroep_versie: Type[Stelselgroepversie] = import_class(
            f"woningwaardering.stelsels.{stelsel.name}.{stelselgroep.name}",
            geldige_stelselgroep_versie_config.class_naam,
            Stelselgroepversie,  # type: ignore[type-abstract] # https://github.com/python/mypy/issues/4717
        )

        return stelselgroep_versie()


class Stelselgroep(_StelselgroepABC):
    """Initialiseert een Stelselgroep.

    Args:
        peildatum (date, optional): De peildatum voor de waardering".
        config (Stelselconfig | None, optional): Een optionele configuratie. Defaults naar None.
    """

    def __init__(
        self,
        peildatum: date = date.today(),
        config: Stelselconfig | None = None,
    ) -> None:
        self.peildatum = peildatum

        if config is None:
            config = Stelselconfig.load(stelsel=self.stelsel)

        self.geldige_versie = self.select_stelselgroepversie(
            self.stelsel, self.stelselgroep, self.peildatum, config
        )

    def bereken(
        self,
        eenheid: EenhedenEenheid,
        woningwaardering_resultaat: (
            WoningwaarderingResultatenWoningwaarderingResultaat | None
        ) = None,
    ) -> WoningwaarderingResultatenWoningwaarderingGroep:
        """Bereken de woningwaardering voor een specifieke eenheid op stelselgroep-niveau.

        Args:
            eenheid (EenhedenEenheid): De eenheid waarvoor de woningwaardering wordt berekend.
            woningwaardering_resultaat (WoningwaarderingResultatenWoningwaarderingResultaat | None, optional): Het resultaat van de woningwaardering.

        Returns:
            WoningwaarderingResultatenWoningwaarderingGroep: Het resultaat van de woningwaardering voor de gehele groep.
        """
        woningwaardering_resultaat = (
            woningwaardering_resultaat
            or WoningwaarderingResultatenWoningwaarderingResultaat()
        )
        return self.geldige_versie.bereken(eenheid, woningwaardering_resultaat)
