from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

import re

from ..remote.parse import (
    parse_bibtex,
    zbmath_external_identifier_url,
    zbmath_external_identifier_parse,
)


def url_builder(doi: str) -> str:
    return f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"


def record_parser(result: str) -> ParsedRecord:
    btx, _ = parse_bibtex(result)
    return (
        btx,
        {"zbl": (zbmath_external_identifier_url, zbmath_external_identifier_parse)},
    )
