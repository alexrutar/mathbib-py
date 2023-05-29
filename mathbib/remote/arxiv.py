from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..remote import ParsedRecord

from datetime import datetime
import re

from bs4 import BeautifulSoup

from .error import RemoteAccessError, RemoteParseError
from .utils import (
    canonicalize_authors,
    zbmath_external_identifier_url,
    zbmath_external_identifier_parse,
    RelatedRecord,
)


REGEX_ARXIV_ID = re.compile(
    r"((?:"
    r"(?:math|bayes-an|stat|cs|funct-an|alg-geom)"
    r"/"
    r"(?:(?:[0-1][0-9])|(?:9[1-9]))(?:0[1-9]|1[0-2])(?:\d{3})(?:v[1-9]\d*)?))"
    r"|"
    r"((?:[0-9][0-9])(?:0[1-9]|1[0-2])(?:[.]\d{4,5}))"
)


def url_builder(arxiv: str) -> str:
    return f"https://export.arxiv.org/api/query?id_list={arxiv}"


def validate_identifier(arxiv: str) -> bool:
    return re.fullmatch(REGEX_ARXIV_ID, arxiv) is not None


def show_url(arxiv: str) -> str:
    return f"https://arxiv.org/abs/{arxiv}"


def download_url(arxiv: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv}.pdf"


def record_parser(result: str) -> ParsedRecord:
    # TODO: sometimes this returns the incorrect record, which needs to be checked

    related = [
        RelatedRecord(
            "zbl", (zbmath_external_identifier_url, zbmath_external_identifier_parse)
        )
    ]

    related = []
    metadata = BeautifulSoup(result, features="xml").entry
    if metadata is None:
        raise RemoteAccessError("Response does not contain entry metadata.")

    dois = metadata.find_all("arxiv:doi")
    if len(dois) > 0 and dois[0].string is not None:
        related.append(RelatedRecord("doi", dois[0].string))

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
