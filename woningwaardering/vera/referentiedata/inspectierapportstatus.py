from woningwaardering.vera.bvg.generated import Referentiedata


class Inspectierapportstatus:
    concept = Referentiedata(
        code="CON",
        naam="Concept",
    )

    definitief = Referentiedata(
        code="DEF",
        naam="Definitief",
    )

    getekend = Referentiedata(
        code="GET",
        naam="Getekend",
    )

    ter_review = Referentiedata(
        code="REV",
        naam="Ter review",
    )

    vervallen = Referentiedata(
        code="VAL",
        naam="Vervallen",
    )