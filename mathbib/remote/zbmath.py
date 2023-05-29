from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ParsedRecord

import re

from bs4 import BeautifulSoup

from .utils import RemoteParseError, RelatedRecord


def url_builder(zbmath: str) -> str:
    return (
        "https://oai.zbmath.org/v1/"
        "?verb=GetRecord"
        f"&identifier=oai:zbmath.org:{zbmath}"
        "&metadataPrefix=oai_zb_preview"
    )


def validate_identifier(zbmath: str) -> bool:
    return 4 <= len(zbmath) <= 8 and zbmath.isnumeric()


def record_parser(result: str) -> ParsedRecord:
    related = []
    metadata = BeautifulSoup(result, features="xml")

    links = [entry.string for entry in metadata.find_all("zbmath:link")]
    arxiv_searched = (
        re.fullmatch(r"https?://arxiv.org/abs/(.+)", link) for link in links
    )
    arxiv_pruned = [match for match in arxiv_searched if match is not None]
    if len(arxiv_pruned) > 0:
        related.append(RelatedRecord("arxiv", str(arxiv_pruned[0].group(1))))

    dois = metadata.find_all("zbmath:doi")
    if len(dois) > 0 and dois[0]:
        related.append(RelatedRecord("doi", dois[0].string))

    out = {
        "author_ids": [entry.string for entry in metadata.find_all("zbmath:author_id")],
        "classifications": sorted(
            entry.string for entry in metadata.find_all("zbmath:classification")
        ),
        "year": metadata.find_all("zbmath:publication_year")[0].string,
    }

    candidate_title = metadata.find_all("zbmath:document_title")[0].string
    if candidate_title is None:
        raise RemoteParseError("Could not identify title.")
    if (
        candidate_title
        != "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
    ):
        out["title"] = candidate_title

    return out, related
