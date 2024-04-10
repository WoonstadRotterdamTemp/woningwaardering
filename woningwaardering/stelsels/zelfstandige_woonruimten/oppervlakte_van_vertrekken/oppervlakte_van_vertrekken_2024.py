from decimal import ROUND_HALF_UP, Decimal

from loguru import logger

from woningwaardering.stelsels.stelselgroepversie import Stelselgroepversie
from woningwaardering.vera.bvg.generated import (
    EenhedenEenheid,
    EenhedenRuimte,
    WoningwaarderingResultatenWoningwaardering,
    WoningwaarderingResultatenWoningwaarderingCriterium,
    WoningwaarderingResultatenWoningwaarderingCriteriumGroep,
    WoningwaarderingResultatenWoningwaarderingGroep,
    WoningwaarderingResultatenWoningwaarderingResultaat,
)
from woningwaardering.vera.referentiedata import (
    Meeteenheid,
    Ruimtedetailsoort,
    Woningwaarderingstelsel,
    Woningwaarderingstelselgroep,
)
from woningwaardering.vera.referentiedata.bouwkundigelementdetailsoort import (
    Bouwkundigelementdetailsoort,
)


def ruimte_is_overige_ruimte(ruimte: EenhedenRuimte) -> bool:
    """Check of de ruimte een overige ruimte is.

    Args:
        ruimte (EenhedenRuimte): een ruimte.

    Returns:
        bool: is de ruimte een overige ruimte.
    """

    def _vertrek_detailsoort(ruimte: EenhedenRuimte) -> bool:
        """Een ruimte telt mogelijk als vertrek indien de ruimte een van de volgende detailsoort is:
        - woonkamer
        - woonkamer en of slaapkamer
        - keuken
        - overig vertrek
        - badkamer
        - badkamer en of toilet
        - doucheruimte
        - zolder
        - slaapkamer

        Args:
            ruimte (EenhedenRuimte): een ruimte

        Returns:
            bool: voldoet de ruimte aan het detailsoort om een vertrek te kunnen zijn.
        """
        if (
            ruimte.detail_soort is None
            or ruimte.detail_soort.code is None
            or ruimte.detail_soort.naam is None
        ):
            return False

        result = ruimte.detail_soort.code in [
            Ruimtedetailsoort.woonkamer.code,
            Ruimtedetailsoort.woon_en_of_slaapkamer.code,
            Ruimtedetailsoort.woonkamer_en_of_keuken.code,
            Ruimtedetailsoort.keuken.code,
            Ruimtedetailsoort.overig_vertrek.code,
            Ruimtedetailsoort.badkamer.code,
            Ruimtedetailsoort.badkamer_en_of_toilet.code,
            Ruimtedetailsoort.doucheruimte.code,
            Ruimtedetailsoort.zolder.code,
            Ruimtedetailsoort.slaapkamer.code,
        ]
        if result is False:
            logger.warning(
                f"{ruimte.detail_soort.naam} {ruimte.detail_soort.code} komt niet in aanmerking voor een puntenwaardering onder {Woningwaarderingstelselgroep.oppervlakte_van_vertrekken.naam}"
            )
        return result

    def _min_2m_hoogte_50_procent_oppervlakte_badkamer_of_doucheruimte(
        ruimte: EenhedenRuimte,
    ) -> bool:
        """De badkamer of doucheruimte heeft over ten minste 50% van de oppervlakte een vrije hoogte van 2,00 m.

        Args:
            ruimte (EenhedenRuimte): een ruimte.

        Returns:
            bool: voldoet de ruimte aan de eis
        """
        if (
            ruimte.detail_soort is None
            or ruimte.oppervlakte is None
            or ruimte.detail_soort.code is None
        ):
            return False

        result = (
            ruimte.inhoud is None
            or (
                ruimte.detail_soort is None
                or ruimte.detail_soort.code
                in [
                    Ruimtedetailsoort.doucheruimte.code,
                    Ruimtedetailsoort.badkamer.code,
                ]
            )
            or (
                ruimte.oppervlakte is None
                or ruimte.inhoud >= ruimte.oppervlakte / 2 * 2
            )
        )
        if result is False:
            logger.warning(
                f"{ruimte.naam} {ruimte.detail_soort.code} heeft een te lage plafondhoogte en krijgt daarom geen punten."
            )
        return result

    def _min_2m10_hoogte_50_procent_oppervlakte(ruimte: EenhedenRuimte) -> bool:
        """De ruimte heeft over ten minste 50% van de oppervlakte een vrije hoogte van 2,10 m.

        Args:
            ruimte (EenhedenRuimte): een ruimte.

        Returns:
            bool: voldoet de ruimte aan de eis
        """
        if (
            ruimte.oppervlakte is None
            or ruimte.detail_soort is None
            or ruimte.detail_soort.code is None
        ):
            return False

        result = (
            ruimte.inhoud is None
            or ruimte.inhoud
            >= (
                ruimte.oppervlakte
                + int(
                    ruimte.detail_soort.code
                    == Ruimtedetailsoort.badkamer_en_of_toilet.code  # correctie voor eerder toegepast: "Indien een toilet in een badruimte of doucheruimte is geplaatst, wordt de oppervlakte van die ruimte met 1m2 verminderd."
                )
            )
            / 2
            * 2.1
            or ruimte.detail_soort.code
            in [Ruimtedetailsoort.doucheruimte.code, Ruimtedetailsoort.badkamer.code]
        )
        if result is False:
            logger.warning(
                f"{ruimte.naam} {ruimte.detail_soort.code} heeft een te lage plafondhoogte en krijgt daarom geen punten."
            )
        return result

    def _min_0komma64m2_badkamer_en_of_toilet(ruimte: EenhedenRuimte) -> bool:
        """Voor gecombineerde bad-/doucheruimte met toilet geldt een minimale oppervlakte van 0,64 m².

        Args:
            ruimte (EenhedenRuimte): een ruimte.

        Returns:
            bool: voldoet de ruimte aan de eis
        """
        if (
            ruimte.oppervlakte is None
            or ruimte.detail_soort is None
            or ruimte.detail_soort.code is None
        ):
            return False

        result = (
            ruimte.detail_soort.code != Ruimtedetailsoort.badkamer_en_of_toilet.code
            or ruimte.oppervlakte >= 0.64
        )
        if result is False:
            logger.warning(
                f"{ruimte.naam} {ruimte.detail_soort} is kleiner dan 0.64 vierkante meter ({ruimte.oppervlakte}) en krijgt daarom geen punten."
            )
        return result

    def _min_4m2_exclusief_keuken_en_badkamer_en_of_toilet(
        ruimte: EenhedenRuimte,
    ) -> bool:
        """Een ruimte moet minimaal 4m2 zijn om te tellen als vertrek. De eisen van minimaal 4m2 gelden niet voor de keuken en badkamer en/of toilet.

        Args:
            ruimte (EenhedenRuimte): een ruimte.

        Returns:
            bool: voldoet de ruimte aan de eis
        """
        if (
            ruimte.oppervlakte is None
            or ruimte.detail_soort is None
            or ruimte.detail_soort.code is None
        ):
            return False

        result = ruimte.oppervlakte >= 4 or ruimte.detail_soort.code in [
            Ruimtedetailsoort.keuken.code,
            Ruimtedetailsoort.badkamer_en_of_toilet.code,
            Ruimtedetailsoort.badkamer.code,
            Ruimtedetailsoort.toiletruimte.code,
        ]
        if result is False:
            logger.warning(
                f"{ruimte.naam} {ruimte.detail_soort.code} is kleiner dan 4 vierkante meter ({ruimte.oppervlakte}) en krijgt daarom geen punten."
            )
        return result

    def _zolder_heeft_vaste_trap(ruimte: EenhedenRuimte) -> bool:
        """Check of een zolder een vaste trap heeft.

        Args:
            ruimte (EenhedenRuimte): Het vertrek om te checken.

        Returns:
            bool: True als de zolder een vaste heeft, False otherwise.
        """
        if ruimte.detail_soort is not None:
            if ruimte.detail_soort.code == Ruimtedetailsoort.zolder.code:
                vaste_trap = [
                    element.detail_soort
                    for element in ruimte.bouwkundige_elementen or []
                    if element.detail_soort
                    and element.detail_soort.code
                    == Bouwkundigelementdetailsoort.trap.code
                ]
                if not vaste_trap:
                    logger.warning(
                        f"Geen vaste trap gevonden in {ruimte.naam} ({ruimte.id}): telt niet mee voor oppervlakte van vertrekken"
                    )
                    return False
        logger.warning(
            f"Vaste trap gevonden in {ruimte.naam} ({ruimte.id}): telt mee voor oppervlakte van vertrekken"
        )
        return True

    if ruimte.soort is None or ruimte.detail_soort is None:
        logger.error(
            f"Ruimte {ruimte} heeft geen soort en/of detailsoort en kan daardoor niet meegerekend worden."
        )

    if not _vertrek_detailsoort(ruimte):
        return True

    if not _min_2m_hoogte_50_procent_oppervlakte_badkamer_of_doucheruimte(ruimte):
        return True

    if not _min_2m10_hoogte_50_procent_oppervlakte(ruimte):
        return True

    if not _min_0komma64m2_badkamer_en_of_toilet(ruimte):
        return True

    if not _min_4m2_exclusief_keuken_en_badkamer_en_of_toilet(ruimte):
        return True

    if not _zolder_heeft_vaste_trap(ruimte):
        return True

    return False


class OppervlakteVanVertrekken2024(Stelselgroepversie):
    @staticmethod
    def bereken(
        eenheid: EenhedenEenheid,
        woningwaardering_resultaat: (
            WoningwaarderingResultatenWoningwaarderingResultaat | None
        ) = None,
    ) -> WoningwaarderingResultatenWoningwaarderingGroep:
        woningwaardering_groep = WoningwaarderingResultatenWoningwaarderingGroep(
            criteriumGroep=WoningwaarderingResultatenWoningwaarderingCriteriumGroep(
                stelsel=Woningwaarderingstelsel.zelfstandige_woonruimten.value,
                stelselgroep=Woningwaarderingstelselgroep.oppervlakte_van_vertrekken.value,
            )
        )

        woningwaardering_groep.woningwaarderingen = []

        for ruimte in eenheid.ruimten or []:
            logger.debug(f"Processsing ruimte: {ruimte}")
            if ruimte.oppervlakte is None:
                logger.warning(f"Ruimte {ruimte} heeft geen oppervlakte")
                continue
            if ruimte.detail_soort is None:
                logger.warning(f"Ruimte {ruimte} heeft geen detailsoort")
                continue
            if ruimte.detail_soort.code is None:
                logger.warning(f"Ruimte {ruimte} heeft geen detailsoortcode")
                continue

            # Indien een toilet in een badruimte of doucheruimte is geplaatst, wordt de oppervlakte van die ruimte met 1m2 verminderd.
            if ruimte.detail_soort.code == Ruimtedetailsoort.badkamer_en_of_toilet.code:
                ruimte.oppervlakte = float(Decimal(ruimte.oppervlakte) - Decimal("1"))
                logger.debug(
                    "Toilet in badkamer gevonden. 1m2 in mindering gebracht van de oppervlakte van de ruimte."
                )

            if ruimte_is_overige_ruimte(ruimte):
                continue

            woningwaardering = WoningwaarderingResultatenWoningwaardering()

            woningwaardering.criterium = (
                WoningwaarderingResultatenWoningwaarderingCriterium(
                    meeteenheid=Meeteenheid.vierkante_meter_m2.value,
                    naam=ruimte.naam,
                )
            )

            woningwaardering.aantal = float(
                Decimal(ruimte.oppervlakte).quantize(Decimal("0.01"), ROUND_HALF_UP)
            )
            logger.debug(
                f"{woningwaardering.aantal} punten voor {ruimte.naam} met een oppervlakte van {ruimte.oppervlakte}"
            )

            woningwaardering_groep.woningwaarderingen.append(woningwaardering)

        punten = Decimal(
            sum(
                Decimal(woningwaardering.aantal)
                for woningwaardering in woningwaardering_groep.woningwaarderingen or []
                if woningwaardering.aantal is not None
            )
        ).quantize(Decimal("1"), ROUND_HALF_UP) * Decimal("1")

        woningwaardering_groep.punten = float(punten)
        return woningwaardering_groep


if __name__ == "__main__":
    f = open("./data_modellen/input/zelfstandige_woonruimten/zolder_vertrek.json", "r+")
    eenheid = EenhedenEenheid.model_validate_json(f.read())
    woningwaardering_resultaat = WoningwaarderingResultatenWoningwaarderingResultaat()
    print(
        OppervlakteVanVertrekken2024.bereken(
            eenheid, woningwaardering_resultaat
        ).model_dump_json(by_alias=True, indent=2, exclude_none=False)
    )