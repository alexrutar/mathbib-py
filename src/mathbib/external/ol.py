from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord


def url_builder(ol: str) -> str:
    match ol[-1]:
        case "M":
            return f"https://openlibrary.org/books/{ol}.json"
        case "W":
            return f"https://openlibrary.org/works/{ol}.json"
        case _:
            raise ValueError(f"Improper ol record {ol}")


def record_parser(result: str) -> ParsedRecord:
    # TODO: parse the result (it's just JSON)
    return {}, {}
