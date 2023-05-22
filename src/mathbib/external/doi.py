from __future__ import annotations
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..remote import ParsedRecord

from ..remote.parse import parse_bibtex


def url_builder(doi: str) -> str:
    return f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"


def doi_to_zbl_url(doi: str) -> str:
    return f"https://zbmath.org/?q=en:{doi}"


def doi_to_zbl_parse(result: str) -> str | None:
    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)


def record_parser(result: str) -> ParsedRecord:
    btx, _ = parse_bibtex(result)
    return (btx, {"zbl": (doi_to_zbl_url, doi_to_zbl_parse)})
