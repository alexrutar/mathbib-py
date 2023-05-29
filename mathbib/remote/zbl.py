from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParsedRecord

from .utils import parse_bibtex


def url_builder(zbl: str) -> str:
    return f"https://zbmath.org/bibtex/{zbl}.bib"


def show_url(zbl: str) -> str:
    return f"https://zbmath.org/{zbl}"


def validate_identifier(zbl: str) -> bool:
    split = zbl.split(".")
    return (len(split) == 1 and zbl.isnumeric()) or (
        len(split) == 2 and split[0].isnumeric() and split[1].isnumeric()
    )


def record_parser(result: str) -> ParsedRecord:
    return parse_bibtex(result)
