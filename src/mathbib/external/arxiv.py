from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

from datetime import datetime
import re

from bs4 import BeautifulSoup

from ..remote import RemoteAccessError, RemoteParseError
from ..remote.parse import canonicalize_authors


def url_builder(arxiv: str) -> str:
    return f"https://export.arxiv.org/api/query?id_list={arxiv}"


def record_parser(result: str) -> ParsedRecord:
    related = {}
    metadata = BeautifulSoup(result, features="xml").entry
    if metadata is None:
        raise RemoteAccessError("Response does not contain entry metadata.")

    dois = metadata.find_all("arxiv:doi")
    if len(dois) > 0 and dois[0].string is not None:
        related["doi"] = dois[0].string

    published = metadata.published
    if published is None:
        raise RemoteParseError("Failed to find publication date tag.")
    date_str = published.string
    if date_str is None:
        raise RemoteParseError("Failed to find publication date tag.")
    try:
        year = datetime.fromisoformat(date_str).strftime("%Y")
    except ValueError as e:
        raise RemoteParseError("Failed to parse publication date '{date_str}'") from e

    arxiv_id = metadata.id
    if arxiv_id is None:
        raise RemoteParseError("Failed to find version tag.")
    arxiv_link = arxiv_id.string
    if arxiv_link is None:
        raise RemoteParseError("Failed to find version tag.")
    arxiv_id_search = re.fullmatch(
        r"https?://arxiv.org/abs/.+v([1-9][0-9]*)", arxiv_link
    )
    if arxiv_id_search is None:
        raise RemoteParseError("Failed to find version.")

    classifications = sorted(
        re.findall(
            r"((?:math|stat|cs)\.[A-Z][A-Z]|\d\d[A-Z]\d\d)",
            " ".join(entry["term"] for entry in metadata.find_all("category")),
        )
    )

    return {
        "arxiv_version": int(arxiv_id_search.group(1)),
        "authors": canonicalize_authors(
            entry.string for entry in metadata.find_all("name")
        ),
        "title": " ".join(metadata.find_all("title")[0].string.split()),
        "classifications": classifications,
        "year": year,
        "bibtype": "preprint",
    }, related
