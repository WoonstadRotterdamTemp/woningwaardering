from decimal import Decimal

from loguru import logger


from woningwaardering.stelsels.stelselgroepversie import Stelselgroepversie
from woningwaardering.vera.referentiedata.eenheidmonument import Eenheidmonument
from .beschermd_monument_bmz import BeschermdMonumentBmz
from woningwaardering.vera.bvg.generated import (
    EenhedenEenheid,
    WoningwaarderingResultatenWoningwaardering,
    WoningwaarderingResultatenWoningwaarderingCriterium,
    WoningwaarderingResultatenWoningwaarderingCriteriumGroep,
    WoningwaarderingResultatenWoningwaarderingGroep,
    WoningwaarderingResultatenWoningwaarderingResultaat,
)
from woningwaardering.vera.referentiedata import (
    Woningwaarderingstelsel,
    Woningwaarderingstelselgroep,
)


class BeschermdMonumentBmzJul2024(Stelselgroepversie):
    def bereken(
        self,
        eenheid: EenhedenEenheid,
        woningwaardering_resultaat: (
            WoningwaarderingResultatenWoningwaarderingResultaat | None
        ) = None,
    ) -> WoningwaarderingResultatenWoningwaarderingGroep:
        woningwaardering_groep = WoningwaarderingResultatenWoningwaarderingGroep(
            criteriumGroep=WoningwaarderingResultatenWoningwaarderingCriteriumGroep(
                stelsel=Woningwaarderingstelsel.zelfstandige_woonruimten.value,
                stelselgroep=Woningwaarderingstelselgroep.beschermd_monument_bmz.value,
            )
        )

        woningwaardering_groep.woningwaarderingen = []

        if eenheid.monumenten is None:
            logger.info(
                f"Monumenten is None voor eenheid {eenheid.id}. De api van cultureelerfgoed wordt geraadpleegd."
            )

            BeschermdMonumentBmz.update_eenheid_monumenten(eenheid)

        if any(
            monument.code == Eenheidmonument.rijksmonument.code
            for monument in eenheid.monumenten or []
        ):
            woningwaardering_groep.woningwaarderingen.append(
                WoningwaarderingResultatenWoningwaardering(
                    criterium=WoningwaarderingResultatenWoningwaarderingCriterium(
                        naam=Eenheidmonument.rijksmonument.naam,
                    ),
                    opslagpercentage=0.3,
                )
            )

        opslagpercentage = Decimal(
            sum(
                Decimal(str(woningwaardering.opslagpercentage))
                for woningwaardering in woningwaardering_groep.woningwaarderingen or []
                if woningwaardering.opslagpercentage is not None
            )
        )

        woningwaardering_groep.opslagpercentage = float(opslagpercentage)
        return woningwaardering_groep
