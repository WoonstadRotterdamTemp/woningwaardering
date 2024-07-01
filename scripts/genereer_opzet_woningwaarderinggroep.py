from datetime import date
from pathlib import Path
import string
import inquirer  # noqa
import locale
from jinja2 import Environment, PackageLoader, select_autoescape
from loguru import logger

from woningwaardering.stelsels.config.config import (
    Stelselconfig,
    Stelselgroepconfig,
    Stelselgroepversieconfig,
)
from woningwaardering.vera.referentiedata import (
    Woningwaarderingstelsel,
    Woningwaarderingstelselgroep,
)


locale.setlocale(locale.LC_ALL, "nl_NL")

environment = Environment(
    loader=PackageLoader("woningwaardering"),
    autoescape=select_autoescape(),
    keep_trailing_newline=True,
)


def validate_date(answers: dict[str, str], answer: str) -> bool:
    try:
        date.fromisoformat(answer)
        return True
    except (TypeError, ValueError):
        return False


def check_write(file_path: Path) -> bool:
    write_file = False

    if file_path.exists():
        print(f"{file_path} bestaat al.")
        overwrite = inquirer.text(message="Type 'Ja' om te overschrijven")
        if overwrite == "Ja":
            write_file = True
    else:
        write_file = True

    return write_file


questions = [
    inquirer.List(
        "stelsel",
        message="Welk stelsel wil je implementeren?",
        choices=[(stelsel.naam, stelsel.name) for stelsel in Woningwaarderingstelsel],
    ),
    inquirer.List(
        "stelselgroep",
        message="Welke stelselgroep wil je implementeren?",
        choices=lambda answers: [
            (stelselgroep.naam, stelselgroep.name)
            for stelselgroep in Woningwaarderingstelselgroep
            if stelselgroep.value.parent is not None
            and stelselgroep.value.parent.code
            == Woningwaarderingstelsel[answers.get("stelsel")].code
        ],
    ),
    inquirer.Text(
        "begindatum",
        message=lambda answers: f"Vanaf welke datum is de {Woningwaarderingstelselgroep[answers.get('stelselgroep')].naam} stelselgroep geldig?",
        default=date.today(),
        validate=validate_date,
    ),
]

answers = inquirer.prompt(questions)

stelsel = str(answers.get("stelsel"))
stelselgroep = str(answers.get("stelselgroep"))
begindatum = date.fromisoformat(answers.get("begindatum"))
woningwaarderingstelsel = Woningwaarderingstelsel[stelsel]
woningwaarderingstelselgroep = Woningwaarderingstelselgroep[stelselgroep]

if woningwaarderingstelselgroep.value.naam is None:
    raise TypeError(f"{woningwaarderingstelselgroep} heeft geen naam")

stelselgroep_class_naam = string.capwords(
    woningwaarderingstelselgroep.name, "_"
).replace("_", "")

stelsels_folder = Path("woningwaardering") / "stelsels"
stelsel_folder = stelsels_folder / stelsel
stelsel_file_path = stelsel_folder / f"{stelsel}.py"

stelsel_class_naam = string.capwords(woningwaarderingstelsel.name, "_").replace("_", "")

if check_write(stelsel_file_path):
    stelsel_template = environment.get_template("stelsels/stelsel/stelsel.py.j2")
    stelsel_result = stelsel_template.render(
        className=stelsel_class_naam,
        stelsel=woningwaarderingstelsel,
    )
    stelsel_folder.mkdir(parents=True, exist_ok=True)
    stelsel_file = stelsel_file_path.write_text(stelsel_result)

stelselconfig: Stelselconfig

stelselgroep_folder = stelsel_folder / stelselgroep
stelselgroep_file_path = stelselgroep_folder / f"{stelselgroep}.py"

if check_write(stelselgroep_file_path):
    stelselgroep_template = environment.get_template(
        "stelsels/stelsel/stelselgroep/stelselgroep.py.j2"
    )

    stelselgroep_result = stelselgroep_template.render(
        className=stelselgroep_class_naam,
        stelsel=woningwaarderingstelsel,
        stelselgroep=woningwaarderingstelselgroep,
    )
    stelselgroep_folder.mkdir(parents=True, exist_ok=True)
    stelselgroep_file_path.write_text(stelselgroep_result)

stelselgroepversie_module = (
    f"{stelselgroep}_{begindatum.strftime('%b').lower()}_{begindatum.year}"
)

stelselgroepversie_file_path = stelselgroep_folder / f"{stelselgroepversie_module}.py"

if check_write(stelselgroepversie_file_path):
    stelselgroepversie_template = environment.get_template(
        "stelsels/stelsel/stelselgroep/stelselgroepversie.py.j2"
    )
    stelselgroepversie_result = stelselgroepversie_template.render(
        className=f"{stelselgroep_class_naam}{begindatum.strftime('%b').capitalize()}{begindatum.year}",
        stelsel=woningwaarderingstelsel,
        stelselgroep=woningwaarderingstelselgroep,
    )
    stelselgroep_folder.mkdir(parents=True, exist_ok=True)
    stelselgroepversie_file_path.write_text(stelselgroepversie_result)

if Path(f"woningwaardering/stelsels/config/{stelsel}.yml").exists():
    stelselconfig = Stelselconfig.load(woningwaarderingstelsel)
else:
    stelselconfig = Stelselconfig(
        stelsel=woningwaarderingstelsel.name,
        begindatum=begindatum,
        stelselgroepen={},
    )

stelselgroepconfig = stelselconfig.stelselgroepen.get(stelselgroep)

if stelselgroepconfig is None:
    stelselgroepconfig = Stelselgroepconfig(
        module=stelselgroep,
        class_naam=stelselgroep_class_naam,
        begindatum=begindatum,
        versies=[],
    )
    stelselconfig.stelselgroepen[stelselgroep] = stelselgroepconfig

stelselgroepversie_class_naam = f"{stelselgroep_class_naam}{begindatum.strftime('%b').capitalize()}{begindatum.year}"

stelselgroepconfig.versies = stelselgroepconfig.versies or []

stelselgroepversieconfig = (
    next(
        (
            versie
            for versie in stelselgroepconfig.versies
            if versie.class_naam == stelselgroepversie_class_naam
        ),
        None,
    )
    if stelselgroepconfig is not None and stelselgroepconfig.versies is not None
    else None
)

if stelselgroepversieconfig is None:
    stelselgroepconfig.versies.append(
        Stelselgroepversieconfig(
            module=stelselgroepversie_module,
            class_naam=stelselgroepversie_class_naam,
            begindatum=begindatum,
        )
    )
    stelselconfig.save()
else:
    logger.info(f"Configuratie voor {stelselgroepversieconfig.class_naam} bestaat al")

stelselgroep_init_template = environment.get_template(
    "stelsels/stelsel/stelselgroep/__init__.py.j2"
)

stelselgroep_init_result = stelselgroep_init_template.render(
    stelselgroep=stelselgroep, stelselgroepconfig=stelselgroepconfig
)

(stelselgroep_folder / "__init__.py").write_text(stelselgroep_init_result)

stelsel_init_template = environment.get_template("stelsels/stelsel/__init__.py.j2")

stelsel_init_result = stelsel_init_template.render(
    className=stelsel_class_naam, stelselconfig=stelselconfig
)

(stelsel_folder / "__init__.py").write_text(stelsel_init_result)
