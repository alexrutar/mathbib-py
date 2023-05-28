from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParsedRecord

import json
import re

from stdnum import isbn

from .utils import (
    zbmath_external_identifier_url,
    zbmath_external_identifier_parse,
    RelatedRecord,
)


def url_builder(isbn_str: str) -> str:
    return (
        "https://openlibrary.org/api/books?"
        f"bibkeys=ISBN:{isbn.format(isbn_str)}&format=json"
    )


def show_url(isbn_str: str) -> str:
    return f"https://openlibrary.org/isbn/{isbn.compact(isbn_str)}"


def validate_identifier(isbn_str: str) -> bool:
    check_valid = isbn.is_valid(isbn_str)
    check_split = "" not in isbn.split(isbn_str)
    return check_valid and check_split


def isbn_to_zbmath_url(isbn_str: str) -> str:
    return zbmath_external_identifier_url(isbn.format(isbn_str))


def record_parser(result: str) -> ParsedRecord:
    record = {}
    related = [
        RelatedRecord("zbl", (isbn_to_zbmath_url, zbmath_external_identifier_parse))
    ]
    res_parsed = json.loads(result)
    try:
        first_entry = next(iter(res_parsed.values()))["info_url"]
        match = re.search(r"\/(OL\d+[WM])\/", first_entry)

        if match is not None:
            ol_related = str(match.group(1))
            related.append(RelatedRecord("ol", ol_related))
            if ol_related[-1] == "M":
                record["bibtype"] = "book"

    except StopIteration:
        pass

    return record, related
