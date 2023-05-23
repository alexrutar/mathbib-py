from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

import json

import re
from urllib.parse import quote

from ..remote.parse import (
    zbmath_external_identifier_url,
    zbmath_external_identifier_parse,
)


def url_builder(isbn: str) -> str:
    return f"https://openlibrary.org/api/books?bibkeys=ISBN:{quote(isbn)}&format=json"


def record_parser(result: str) -> ParsedRecord:
    related = {
        "zbl": (zbmath_external_identifier_url, zbmath_external_identifier_parse)
    }
    res_parsed = json.loads(result)
    try:
        first_entry = next(iter(res_parsed.values()))["info_url"]
        match = re.search(r"\/(OL\d+[WM])\/", first_entry)

        if match is not None:
            related["ol"] = str(match.group(1))

    except StopIteration:
        pass

    return {}, related
