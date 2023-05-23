from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

from dataclasses import dataclass

from xdg_base_dirs import xdg_data_home

from . import doi, zbl, arxiv, zbmath
from ..remote import RemoteRecord, RemoteKey


REMOTES: Final = {
    RemoteKey.ZBL: RemoteRecord("zbl", zbl.url_builder, zbl.record_parser),
    RemoteKey.DOI: RemoteRecord("doi", doi.url_builder, doi.record_parser),
    RemoteKey.ZBMATH: RemoteRecord("zbmath", zbmath.url_builder, zbmath.record_parser),
    RemoteKey.ARXIV: RemoteRecord("arxiv", arxiv.url_builder, arxiv.record_parser),
}


@dataclass(order=True, frozen=True)
class KeyId:
    key: RemoteKey
    identifier: str

    @classmethod
    def from_keyid(cls, keyid: str) -> KeyId:
        tokens = keyid.split(":")
        if len(tokens) >= 2:
            try:
                return cls(RemoteKey[tokens[0].upper()], ":".join(tokens[1:]))
            except KeyError:
                pass

        raise ValueError(f"Invalid KEY:ID pair '{keyid}'")

    def toml_path(self):
        return (
            xdg_data_home()
            / "mathbib"
            / "records"
            / str(self.key)
            / f"{self.identifier}.toml"
        )

    def file_path(self, suffix: str = "pdf"):
        return (
            xdg_data_home()
            / "mathbib"
            / "files"
            / str(self.key)
            / f"{self.identifier}.{suffix}"
        )

    def __str__(self):
        return f"{self.key}:{self.identifier}"

    def __repr__(self):
        return f"{self.key}:{self.identifier}"


# def (key: str) -> int:
#     """Relative priority of entry types."""
#     match key:
#         case "zbl":
#             return 3

#         case "doi":
#             return 2

#         case "zbmath":
#             return 1

#         case "arxiv":
#             return 0

#         case _:
#             return -1


# def (key_id: str) -> tuple[str, str]:
#     tokens = key_id.split(":")
#     if tokens[0] in REMOTES.keys() and len(tokens) >= 2:
#         return (tokens[0], ":".join(tokens[1:]))

#     raise ValueError(f"Invalid key:identifier pair '{key_id}'")
