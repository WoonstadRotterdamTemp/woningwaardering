from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from importlib.resources import files

import pandas as pd

from woningwaardering.stelsels.config import Stelselconfig
from woningwaardering.stelsels.stelselgroep import (
    Stelselgroep,
)
from woningwaardering.stelsels.utils import (
    filter_dataframe_op_datum,
    import_class,
    is_geldig,
)
from woningwaardering.vera.bvg.generated import (
    EenhedenEenheid,
    WoningwaarderingResultatenWoningwaarderingResultaat,
)
from woningwaardering.vera.referentiedata import (
    Woningwaarderingstelsel,
)


class Stelsel:
    """Initialiseert een Stelsel object.

    Parameters:
        stelsel (Woningwaarderingstelsel): Het stelsel dat wordt berekend.
        peildatum (date, optional): De peildatum voor de waardering.
            Standaard is de huidige datum.
    """

    def __init__(
        self,
        stelsel: Woningwaarderingstelsel,
        peildatum: date = date.today(),
    ) -> None:
        self.stelsel = stelsel
        self.peildatum = peildatum
        self.stelsel_config = Stelselconfig.load(stelsel=self.stelsel)
        self.geldige_stelselgroepen = self.select_geldige_stelselgroepen(
            self.peildatum,
            self.stelsel,
            self.stelsel_config,
        )
        self.df_maximale_huur = pd.read_csv(
            files("woningwaardering").joinpath(
                f"stelsels/{stelsel.name}/maximale_huurprijzen.csv"
            )
        ).pipe(filter_dataframe_op_datum, peildatum)

    def bereken(
        self,
        eenheid: EenhedenEenheid,
    ) -> WoningwaarderingResultatenWoningwaarderingResultaat:
        """Berekent de woningwaardering voor een stelsel.

        Parameters:
            eenheid (EenhedenEenheid): De eenheid waarvoor de woningwaardering wordt berekend.

        Returns:
            WoningwaarderingResultatenWoningwaarderingResultaat: Het bijgewerkte resultaat van de woningwaardering.
        """

        resultaat = WoningwaarderingResultatenWoningwaarderingResultaat()
        resultaat.stelsel = self.stelsel.value

        resultaat.groepen = []

        for stelselgroep_versie in self.geldige_stelselgroepen:
            resultaat.groepen.append(stelselgroep_versie.bereken(eenheid, resultaat))

        # Het puntentotaal per woning wordt na eindsaldering (met inbegrip van de bij
        # zorgwoningen geldende toeslag) afgerond op hele punten. Bij 0,5 punten of
        # meer wordt afgerond naar boven op hele punten, bij minder dan 0,5 punten
        # wordt afgerond naar beneden op hele punten.
        #
        # https://wetten.overheid.nl/BWBR0003237/2024-01-01#BijlageI_DivisieA_Divisie_Divisie15

        resultaat.punten = float(
            Decimal(
                sum(
                    woningwaardering_groep.punten
                    for woningwaardering_groep in resultaat.groepen or []
                    if woningwaardering_groep.punten is not None
                )
            ).quantize(Decimal("1"), ROUND_HALF_UP)
        )

        resultaat.opslagpercentage = (
            sum(
                woningwaardering_groep.opslagpercentage
                for woningwaardering_groep in resultaat.groepen or []
                if woningwaardering_groep.opslagpercentage is not None
            )
            or None
        )

        maximale_huur = self.bereken_maximale_huur(resultaat)

        resultaat.maximale_huur = float(maximale_huur)

        if resultaat.opslagpercentage is not None:
            resultaat.huurprijsopslag = float(
                (maximale_huur * Decimal(str(resultaat.opslagpercentage))).quantize(
                    Decimal("0.01"), ROUND_HALF_UP
                )
            )

        resultaat.maximale_huur_inclusief_opslag = float(
            maximale_huur + Decimal(str(resultaat.huurprijsopslag or 0))
        )

        return resultaat

    def bereken_maximale_huur(
        self, resultaat: WoningwaarderingResultatenWoningwaarderingResultaat
    ) -> Decimal:
        punten = Decimal(str(resultaat.punten))

        df_maximale_huur = self.df_maximale_huur

        begrensde_punten = min(
            max(punten, df_maximale_huur["Punten"].min()),
            df_maximale_huur["Punten"].max(),
        )

        maximale_huur = Decimal(
            df_maximale_huur[df_maximale_huur["Punten"] == begrensde_punten][
                "Bedrag"
            ].item()
        )

        hoogste_twee = df_maximale_huur.nlargest(2, "Punten")
        hoogste_punten = hoogste_twee.iloc[0]["Punten"]
        hoogste_bedrag = Decimal(hoogste_twee.iloc[0]["Bedrag"])
        een_na_hoogste_bedrag = Decimal(hoogste_twee.iloc[1]["Bedrag"])

        bedrag_verschil = hoogste_bedrag - een_na_hoogste_bedrag

        punten_boven_hoogste = max(punten - hoogste_punten, Decimal(0))
        aanvullende_waarde = punten_boven_hoogste * bedrag_verschil

        maximale_huur += aanvullende_waarde

        return maximale_huur

    @staticmethod
    def select_geldige_stelselgroepen(
        peildatum: date,
        stelsel: Woningwaarderingstelsel,
        config: Stelselconfig | None = None,
    ) -> list[Stelselgroep]:
        """Selecteert de geldige stelselgroepen voor een peildatum en een stelsel.

        Parameters:
            peildatum (date): De peildatum voor de waardering.
            stelsel (Woningwaarderingstelsel): Het stelsel dat wordt berekend.
            config (Stelselconfig | None, optional): Het configuratiebestand voor het stelsel.
                Standaard is None, wat betekent dat het configuratiebestand wordt geladen.

        Returns:
            list[Stelselgroep]: Een lijst met de geldige stelselgroepen.

        Raises:
            ValueError: Als het stelsel niet geldig is op de peildatum.
            ValueError: Als er geen geldige stelselgroepen zijn gevonden.
        """
        if config is None:
            config = Stelselconfig.load(stelsel=stelsel)
        if not is_geldig(
            config.begindatum,
            config.einddatum,
            peildatum,
        ):
            raise ValueError(
                f"stelsel {stelsel.value.naam} met begindatum {config.begindatum} en einddatum {config.einddatum} is niet geldig op peildatum {peildatum}."
            )

        geldige_stelselgroepen: list[Stelselgroep] = [
            import_class(
                f"woningwaardering.stelsels.{stelsel.name}",
                stelgroep_config.class_naam,
                Stelselgroep,
            )(
                peildatum=peildatum,
            )
            for _, stelgroep_config in config.stelselgroepen.items()
            if is_geldig(
                stelgroep_config.begindatum,
                stelgroep_config.einddatum,
                peildatum,
            )
        ]

        if not geldige_stelselgroepen:
            raise ValueError(
                f"geen geldige stelselgroepen gevonden voor {stelsel.value.naam} met peildatum {peildatum}"
            )

        return geldige_stelselgroepen
