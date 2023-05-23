from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Iterable

from nameparser import HumanName
import re

from .journal_abbreviations import JOURNALS
from ..bibtex import BibTexHandler
from . import RemoteParseError


def zbmath_external_identifier_url(identifier: str) -> str:
    return f"https://zbmath.org/?q=en:{identifier}"


def zbmath_external_identifier_parse(result: str) -> str | None:
    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)


def parse_journal(journal: str, fjournal: Optional[str] = None):
    normalize = lambda name: name.lower().replace(" ", "_").replace(".", "")

    if fjournal is not None:
        abbrev = JOURNALS.get(normalize(fjournal))

    else:
        abbrev = JOURNALS.get(normalize(journal))

    if abbrev is not None:
        return abbrev
    else:
        return journal


def canonicalize_authors(author_list: Iterable[str]) -> list[str]:
    human_names = [HumanName(author) for author in author_list]
    for hn in human_names:
        hn.capitalize()
    return [f"{hn.last}, {hn.first} {hn.middle}".strip() for hn in human_names]


def parse_bibtex(result: str) -> tuple[dict, dict]:
    bth = BibTexHandler()
    try:
        bibtex_parsed = bth.loads(result).entries[0]
    except IndexError:
        raise RemoteParseError("Could not parse bibtex entry.")

    # capture some keys explicitly from the bibtex file
    captured = (
        "language",
        "issn",
        "number",
        "pages",
        "title",
        "volume",
        "year",
    )

    # drop some keys from the bibtex file
    dropped = (
        "title",
        "url",
        "month",
        "journal",
        "fjournal",
        "ENTRYTYPE",
        "ID",
        "zbl",
        "keywords",
        "author",
        "zbmath",
        "doi",
    )

    # extract some related keys
    related = (
        "zbmath",
        "doi",
        "zbl",
    )

    extracted = {k: v for k, v in bibtex_parsed.items() if k in captured}
    try:
        additional = {
            # save any bibtex keys not captured or dropped
            "bibtex": {
                k: v
                for k, v in bibtex_parsed.items()
                if k not in captured and k not in dropped
            },
            "bibtype": bibtex_parsed["ENTRYTYPE"],
        }
    except KeyError:
        raise RemoteParseError(f"BibLaTeX file missing essential key 'ENTRYTYPE'")

    if "author" in bibtex_parsed.keys():
        additional["authors"] = canonicalize_authors(bibtex_parsed["author"])

    if "journal" in bibtex_parsed.keys():
        additional["journal"] = parse_journal(
            bibtex_parsed["journal"], fjournal=bibtex_parsed.get("fjournal")
        )

    return {**extracted, **additional}, {
        k: v for k, v in bibtex_parsed.items() if k in related
    }
