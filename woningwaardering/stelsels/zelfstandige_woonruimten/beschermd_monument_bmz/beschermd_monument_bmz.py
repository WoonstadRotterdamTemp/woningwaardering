from datetime import date

from loguru import logger
from rdflib import Graph, Literal, Namespace
from rdflib.plugins.sparql import prepareQuery

from woningwaardering.stelsels import utils
from woningwaardering.stelsels.stelselgroep import Stelselgroep
from woningwaardering.vera.bvg.generated import (
    EenhedenEenheid,
)
from woningwaardering.vera.referentiedata import (
    Eenheidmonument,
    Woningwaarderingstelsel,
    Woningwaarderingstelselgroep,
)


CEO = Namespace("https://linkeddata.cultureelerfgoed.nl/def/ceo#")
BAG = Namespace("http://bag.basisregistraties.overheid.nl/bag/id/")

endpoint = "https://api.linkeddata.cultureelerfgoed.nl/datasets/rce/cho/sparql"


query_template = """
ASK
WHERE {{
    SERVICE <{endpoint}> {{
        ?monument a ceo:Rijksmonument .
        ?monument ceo:heeftBasisregistratieRelatie ?basisregistratieRelatie .
        ?basisregistratieRelatie ceo:heeftBAGRelatie ?bagRelatie .
        ?bagRelatie ceo:verblijfsobjectIdentificatie ?verblijfsobjectIdentificatie .
    }}
}}
"""

rijksmonumenten_query = prepareQuery(
    query_template.format(endpoint=endpoint), initNs={"ceo": CEO, "bag": BAG}
)


class BeschermdMonumentBmz(Stelselgroep):
    def __init__(self, peildatum: date = date.today()) -> None:
        self.stelsel = Woningwaarderingstelsel.zelfstandige_woonruimten
        self.stelselgroep = Woningwaarderingstelselgroep.beschermd_monument_bmz
        super().__init__(peildatum=peildatum)

    @staticmethod
    def update_eenheid_monumenten(eenheid: EenhedenEenheid) -> EenhedenEenheid:
        eenheid.monumenten = eenheid.monumenten or []

        if (
            eenheid.adresseerbaar_object_basisregistratie is not None
            and eenheid.adresseerbaar_object_basisregistratie.bag_identificatie
            is not None
        ):
            BeschermdMonumentBmz.is_rijksmonument(
                eenheid.adresseerbaar_object_basisregistratie.bag_identificatie
            )
            is_rijksmonument = BeschermdMonumentBmz.is_rijksmonument(
                eenheid.adresseerbaar_object_basisregistratie.bag_identificatie
            )
            logger.info(
                f"Eenheid {eenheid.id} met verblijfsobjectIdentificatie {eenheid.adresseerbaar_object_basisregistratie.bag_identificatie} is {'een' if is_rijksmonument else 'geen'} rijksmonument volgens de api van cultureelerfgoed."
            )
            if is_rijksmonument:
                eenheid.monumenten.append(Eenheidmonument.rijksmonument.value)

        return eenheid

    @staticmethod
    def is_rijksmonument(verblijfsobjectIdentificatie: str) -> bool:
        if not str.isnumeric(verblijfsobjectIdentificatie):
            raise ValueError("VerblijfsobjectIdentificatie moet numeriek zijn")

        graph = Graph()

        result = graph.query(
            rijksmonumenten_query,
            initBindings={
                "verblijfsobjectIdentificatie": Literal(verblijfsobjectIdentificatie),
            },
        )

        if result is None or result.askAnswer is None:
            return False
        else:
            return result.askAnswer


if __name__ == "__main__":  # pragma: no cover
    logger.enable("woningwaardering")

    beschermd_monument_bmz = BeschermdMonumentBmz()
    with open("tests/data/generiek/input/37101000032.json", "r+") as file:
        eenheid = EenhedenEenheid.model_validate_json(file.read())

        woningwaardering_resultaat = beschermd_monument_bmz.bereken(eenheid)

        print(
            woningwaardering_resultaat.model_dump_json(
                by_alias=True, indent=2, exclude_none=True
            )
        )

        tabel = utils.naar_tabel(woningwaardering_resultaat)

        print(tabel)
