from datetime import date
from pathlib import Path

import pytest
from tests.test_utils import assert_output_model, laad_specifiek_input_en_output_model

from woningwaardering.stelsels.zelfstandige_woonruimten import (
    Renovatie,
)
from woningwaardering.vera.bvg.generated import (
    WoningwaarderingResultatenWoningwaarderingGroep,
)
from woningwaardering.vera.referentiedata import Woningwaarderingstelselgroep

# Get the absolute path to the current file
current_file_path = Path(__file__).absolute().parent


@pytest.fixture(params=[str(p) for p in (current_file_path / "output").rglob("*.json")])
def specifieke_input_en_output_model(request):
    output_file_path = request.param
    return laad_specifiek_input_en_output_model(
        current_file_path, Path(output_file_path)
    )


def test_Renovatie(zelfstandige_woonruimten_inputmodel, woningwaardering_resultaat):
    try:
        renovatie = Renovatie()
        resultaat = renovatie.bereken(
            zelfstandige_woonruimten_inputmodel, woningwaardering_resultaat
        )
        assert isinstance(resultaat, WoningwaarderingResultatenWoningwaarderingGroep)
    except NotImplementedError:
        pytest.skip(
            f"{Woningwaarderingstelselgroep.renovatie.naam} is niet geïmplementeerd voor {date.today()}"
        )


def test_Renovatie_output(
    zelfstandige_woonruimten_input_en_outputmodel,
):
    eenheid_input, eenheid_output, peildatum = (
        zelfstandige_woonruimten_input_en_outputmodel
    )
    try:
        renovatie = Renovatie(peildatum=peildatum)
        resultaat = renovatie.bereken(eenheid_input)
        assert_output_model(
            resultaat,
            eenheid_output,
            Woningwaarderingstelselgroep.renovatie,
        )
    except NotImplementedError:
        pytest.skip(
            f"{Woningwaarderingstelselgroep.renovatie.naam} is niet geïmplementeerd voor {peildatum}"
        )


def test_Renovatie_specifiek_output(specifieke_input_en_output_model):
    eenheid_input, eenheid_output, peildatum = specifieke_input_en_output_model
    try:
        renovatie = Renovatie(peildatum=peildatum)
        resultaat = renovatie.bereken(eenheid_input)

        assert_output_model(
            resultaat,
            eenheid_output,
            Woningwaarderingstelselgroep.renovatie,
        )
    except NotImplementedError:
        pytest.skip(
            f"{Woningwaarderingstelselgroep.renovatie.naam} is niet geïmplementeerd voor {peildatum}"
        )
