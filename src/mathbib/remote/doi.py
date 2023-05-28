from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParsedRecord

import re

from .utils import (
    parse_bibtex,
    zbmath_external_identifier_url,
    zbmath_external_identifier_parse,
    RelatedRecord,
)

REGEX_DOI = re.compile(r"(10\.\d{4,9}(?:/[-._;():a-zA-Z0-9]+)+)|(10.1002(?:/[^\s/]+)+)")


def url_builder(doi: str) -> str:
    return f"https://api.crossref.org/works/{doi}/transform/application/x-bibtex"


def show_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def validate_identifier(doi: str) -> bool:
    return re.fullmatch(REGEX_DOI, doi) is not None


def record_parser(result: str) -> ParsedRecord:
    btx, _ = parse_bibtex(result)
    return (
        btx,
        [
            RelatedRecord(
                "zbl",
                (zbmath_external_identifier_url, zbmath_external_identifier_parse),
            )
        ],
    )
