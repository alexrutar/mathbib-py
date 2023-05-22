from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

from . import doi, zbl, arxiv, zbmath
from ..remote import RemoteRecord

REMOTES: Final = {
    "arxiv": RemoteRecord("arxiv", arxiv.url_builder, arxiv.record_parser),
    "doi": RemoteRecord("doi", doi.url_builder, doi.record_parser),
    "zbl": RemoteRecord("zbl", zbl.url_builder, zbl.record_parser),
    "zbmath": RemoteRecord("zbmath", zbmath.url_builder, zbmath.record_parser),
}


def parse_key_id(key_id: str) -> tuple[str, str]:
    tokens = key_id.split(":")
    if tokens[0] in REMOTES.keys() and len(tokens) >= 2:
        return (tokens[0], ":".join(tokens[1:]))

    raise ValueError(f"Invalid key:identifier pair '{key_id}'")
