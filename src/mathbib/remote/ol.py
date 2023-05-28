from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParsedRecord

import json
import re

from .utils import RelatedRecord


def url_builder(ol: str) -> str:
    match ol[-1]:
        case "M":
            return f"https://openlibrary.org/books/{ol}.json"
        case "W":
            return f"https://openlibrary.org/works/{ol}.json"
        case _:
            raise ValueError(f"Improper ol record '{ol}'")


def show_url(ol: str) -> str:
    match ol[-1]:
        case "M":
            return f"https://openlibrary.org/books/{ol}"
        case "W":
            return f"https://openlibrary.org/works/{ol}"
        case _:
            raise ValueError(f"Improper ol record '{ol}'")


def validate_identifier(ol: str) -> bool:
    return re.fullmatch(r"OL\d+[WM]", ol) is not None


def record_parser(result: str) -> ParsedRecord:
    parsed = json.loads(result)
    record = {}
    related = []
    if "title" in parsed.keys():
        record["title"] = parsed["title"]
    if "isbn_13" in parsed.keys():
        # TODO: if multiple keys, add all
        related = [RelatedRecord("isbn", parsed["isbn_13"][0])]
    return record, related
