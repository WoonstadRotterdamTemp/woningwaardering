from pathlib import Path

import pytest
from test_utils import assert_output_model, laad_specifiek_input_en_output_model

from woningwaardering.stelsels.zelfstandige_woonruimten.oppervlakte_van_overige_ruimten import (
    OppervlakteVanOverigeRuimten,
)

# from woningwaardering.vera.bvg.generated import WoningwaarderingResultatenWoningwaarderingGroep
from woningwaardering.vera.referentiedata import Woningwaarderingstelselgroep


# def test_OppervlakteVanOverigeRuimten(eenheid_inputmodel, woningwaardering_resultaat):
#     ovv = OppervlakteVanOverigeRuimten(peildatum="01-01-2024")
#     resultaat = ovv.bereken(eenheid_inputmodel, woningwaardering_resultaat)
#     assert isinstance(resultaat, WoningwaarderingResultatenWoningwaarderingGroep)


# def test_OppervlakteVanOverigeRuimten_output(eenheid_input_en_output):
#     eenheid_input, eenheid_output, peildatum = eenheid_input_en_output
#     ovv = OppervlakteVanOverigeRuimten(peildatum=peildatum)
#     resultaat = ovv.bereken(eenheid_input)

#     assert_output_model(
#         resultaat,
#         eenheid_output,
#         Woningwaarderingstelselgroep.oppervlakte_van_overige_ruimten,
#     )

# Get the absolute path to the current file
current_file_path = Path(__file__).absolute().parent


@pytest.fixture(
    params=[str(p) for p in (current_file_path / "data/output").rglob("*.json")]
)
def specifieke_input_en_output_model(request):
    output_file_path = request.param
    return laad_specifiek_input_en_output_model(
        current_file_path, Path(output_file_path)
    )


def test_OppervlakteVanOverigeRuimten_specifiek_output(
    specifieke_input_en_output_model,
):
    eenheid_input, eenheid_output, peildatum = specifieke_input_en_output_model
    ovr = OppervlakteVanOverigeRuimten(peildatum=peildatum)
    resultaat = ovr.bereken(eenheid_input)

    assert_output_model(
        resultaat,
        eenheid_output,
        Woningwaarderingstelselgroep.oppervlakte_van_overige_ruimten,
    )