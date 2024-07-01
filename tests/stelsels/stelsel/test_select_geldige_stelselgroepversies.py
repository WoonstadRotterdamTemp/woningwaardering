from datetime import date

import pytest

from woningwaardering.stelsels.stelsel import Stelsel
from woningwaardering.stelsels.stelselgroep import Stelselgroep
from woningwaardering.vera.referentiedata import (
    Woningwaarderingstelsel,
)


@pytest.mark.parametrize(
    "peildatum, stelsel, aantal_geldige_stelselgroepen",
    [
        (
            date(2024, 1, 1),
            Woningwaarderingstelsel.zelfstandige_woonruimten,
            10,
        )
    ],
)
def test_select_geldige_stelselgroepen(
    peildatum, stelsel, aantal_geldige_stelselgroepen
):
    geldigige_stelselgroepen = Stelsel.select_geldige_stelselgroepen(
        peildatum=peildatum, stelsel=stelsel
    )
    assert (
        len(geldigige_stelselgroepen) == aantal_geldige_stelselgroepen
    ), "Aantal geldige stelselgroepen is niet correct."
    for stelselgroep in geldigige_stelselgroepen:
        assert isinstance(
            stelselgroep, Stelselgroep
        ), f"Stelselgroep '{stelselgroep}' is geen instance van Stelselgroep"
