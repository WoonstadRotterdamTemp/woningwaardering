from typing import Iterator
from woningwaardering.vera.bvg.generated import EenhedenRuimte
from woningwaardering.vera.referentiedata import (
    Bouwkundigelementdetailsoort,
    Ruimtedetailsoort,
)


def badruimte_met_toilet(ruimte: EenhedenRuimte) -> bool:
    """
    Controleert of de gegeven `ruimte` een badkamer met een toilet is of een doucheruimte met een toilet.

    Args:
        ruimte (EenhedenRuimte): Het ruimte-object om te controleren.

    Returns:
        bool: True als de ruimte een badkamer met een toilet is of een doucheruimte met een toilet, anders False.

    Raises:
        TypeError: Als de ruimte geen detailsoort heeft.
    """
    if ruimte.detail_soort is None:
        error_msg = f"ruimte.detail_soort is None voor {ruimte.id}"
        raise TypeError(error_msg)
    return (ruimte.detail_soort.code == Ruimtedetailsoort.badkamer_met_toilet.code) or (
        ruimte.detail_soort.code
        in [Ruimtedetailsoort.doucheruimte.code, Ruimtedetailsoort.badkamer.code]
        and heeft_bouwkundig_element(
            ruimte, Bouwkundigelementdetailsoort.closetcombinatie
        )
    )


def get_bouwkundige_elementen_codes(ruimte: EenhedenRuimte) -> Iterator[str]:
    """
    Haalt de lijst met codes van bouwkundige elementen in de ruimte op.

    Args:
        ruimte (EenhedenRuimte): Een ruimte met bouwkundige elementen

    Returns:
        Iterator[str]: Een iterator van de codes van de bouwkundige elementen.
    """
    return (
        element.detail_soort.code
        for element in ruimte.bouwkundige_elementen or []
        if element.detail_soort is not None and element.detail_soort.code is not None
    )


def heeft_bouwkundig_element(
    ruimte: EenhedenRuimte, *bouwkundigelementdetailsoort: Bouwkundigelementdetailsoort
) -> bool:
    """
    Controleert of een ruimte een specifiek bouwkundig element bevat.

    Args:
        ruimte (EenhedenRuimte): De ruimte waarin gecontroleerd moet worden.
        *bouwkundigelementdetailsoort (Bouwkundigelementdetailsoort): De bouwkundige elementen waarop gecontroleerd moet worden.

    Returns:
        bool: True als de ruimte alle opgegeven bouwkundige elementen bevat, anders False.
    """
    ruimte_bouwkundige_elementen_codes = get_bouwkundige_elementen_codes(ruimte)

    return all(
        elementdetailsoort.code in ruimte_bouwkundige_elementen_codes
        for elementdetailsoort in bouwkundigelementdetailsoort
    )


def aantal_bouwkundige_elementen(
    ruimte: EenhedenRuimte, *bouwkundigelementdetailsoort: Bouwkundigelementdetailsoort
) -> int:
    """
    Telt (de combinatie van) het aantal bouwkundige elementen in een ruimte dat overeenkomt met het opgegeven bouwkundige element.

    Args:
        ruimte (EenhedenRuimte): De ruimte waarin geteld moet worden.
        *bouwkundigelementdetailsoort (Bouwkundigelementdetailsoort): De bouwkundige elementen die geteld moeten worden.

    Returns:
        int: Het aantal bouwkundige elementen in de ruimte dat overeenkomt met de opgegeven bouwkundige elementen.
    """
    if len(bouwkundigelementdetailsoort) > 1:
        return min(
            aantal_bouwkundige_elementen(ruimte, detailsoort)
            for detailsoort in bouwkundigelementdetailsoort
        )

    ruimte_bouwkundige_elementen_codes = get_bouwkundige_elementen_codes(ruimte)

    return len(
        list(
            code
            for code in ruimte_bouwkundige_elementen_codes
            if code
            in (detailsoort.code for detailsoort in bouwkundigelementdetailsoort)
        )
    )
