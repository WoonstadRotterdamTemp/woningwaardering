from woningwaardering.vera.bvg.generated import Referentiedata


class Machtigingsoort:
    doorlopend = Referentiedata(
        code="DOO",
        naam="Doorlopend",
    )

    eenmalig = Referentiedata(
        code="EEN",
        naam="Eenmalig",
    )