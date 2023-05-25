from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

from ..remote.parse import parse_bibtex
from urllib.parse import quote


def url_builder(zbl: str) -> str:
    return f"https://zbmath.org/bibtex/{quote(zbl)}.bib"


def validate_identifier(zbl: str) -> bool:
    split = zbl.split(".")
    return (len(split) == 1 and zbl.isnumeric()) or (
        len(split) == 2 and split[0].isnumeric() and split[1].isnumeric()
    )


def record_parser(result: str) -> ParsedRecord:
    return parse_bibtex(result)
