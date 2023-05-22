from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

from ..remote.parse import parse_bibtex


def url_builder(zbl: str) -> str:
    return f"https://zbmath.org/bibtex/{zbl}.bib"


def record_parser(result: str) -> ParsedRecord:
    return parse_bibtex(result)
