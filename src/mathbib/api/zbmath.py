from bs4 import BeautifulSoup
import re

from ..error import RemoteParseError


def url_builder(zbmath: str) -> str:
    return (
        "https://oai.zbmath.org/v1/"
        "?verb=GetRecord"
        f"&identifier=oai:zbmath.org:{zbmath}"
        "&metadataPrefix=oai_zb_preview"
    )


def record_parser(result: str) -> dict:
    metadata = BeautifulSoup(result, features="xml")
    links = [entry.string for entry in metadata.find_all("zbmath:link")]
    arxiv_searched = (
        re.fullmatch(r"https?://arxiv.org/abs/(.+)", link) for link in links
    )
    arxiv_pruned = [match for match in arxiv_searched if match is not None]
    if len(arxiv_pruned) > 0:
        arxiv = arxiv_pruned[0].group(1)
    else:
        arxiv = None

    out = {
        "author_ids": [entry.string for entry in metadata.find_all("zbmath:author_id")],
        "classifications": sorted(
            entry.string for entry in metadata.find_all("zbmath:classification")
        ),
    }
    if arxiv is not None:
        out["arxiv"] = arxiv  # type: ignore

    candidate_title = metadata.find_all("zbmath:document_title")[0].string
    if candidate_title is None:
        raise RemoteParseError("Could not identify title.")
    if (
        candidate_title
        != "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
    ):
        out["title"] = candidate_title

    return out
