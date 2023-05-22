from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Optional

import tomllib
from itertools import chain

from .external import REMOTES, parse_key_id
from .remote import RemoteAccessError
from .search import zbmath_search_doi

from xdg_base_dirs import xdg_data_home


def get_records(
    keyid_pairs: Iterable[tuple[str, str]]
) -> dict[str, tuple[dict, dict[str, str]]]:
    return {key:REMOTES[key].load_record(identifier) for key, identifier in keyid_pairs}


def extract_keyid_pairs(
    to_resolve: Iterable[tuple[dict, dict[str, str]]]
) -> dict[str, str]:
    return {k: v for _, dct in to_resolve for k, v in dct.items()}


def _resolve_all_records(
    keyid_pairs: Iterable[tuple[str, str]], resolved: set[str]
) -> Iterable[tuple[str, dict]]:
    results = get_records(
        ((key, identifier) for key, identifier in keyid_pairs if key not in resolved)
    )
    yield from ((key, rec) for (key, (rec, _)) in results.items())

    resolved.update(k for k, _ in keyid_pairs)
    to_resolve = extract_keyid_pairs(results.values())

    if len(to_resolve) > 0:
        yield from _resolve_all_records(to_resolve.items(), resolved)


def resolve_records(keyid: str) -> dict:
    return {k:v for k,v in _resolve_all_records((parse_key_id(keyid),), set())}


class ArchiveRecord:
    def __init__(self, keyid: str):
        key, identifier = parse_key_id(keyid)
        self.record = remote_record if remote_record is not None else {}
        self.bibtex = self.record.pop("bibtex", {})
        if "authors" in self.record.keys():
            self.record["authors"] = _canonicalize_authors(self.record["authors"])

        self.local_record_folder = xdg_data_home() / "mathbib" / "records"

    @classmethod
    def from_arxiv(cls, arxiv: str):
        return cls(remote_record=REMOTES["arxiv"].load_record(arxiv))

    @classmethod
    def from_zbl(cls, zbl: str):
        zbl_record = REMOTES["zbl"].load_record(zbl)
        zbmath_record = REMOTES["zbmath"].load_record(zbl_record["zbmath"])
        if "arxiv" in zbmath_record.keys():
            arxiv_record = REMOTES["arxiv"].load_record(zbmath_record["arxiv"])
        else:
            arxiv_record = {}

        combined_record = {**arxiv_record, **zbmath_record, **zbl_record}

        return cls(remote_record=combined_record)

    @classmethod
    def from_doi(cls, doi: str):
        zbl = zbmath_search_doi(doi)
        if zbl is not None:
            return cls.from_zbl(zbl)
        else:
            raise RemoteAccessError("Could not find DOI '{doi}'.")

    def as_bibtex(self) -> dict:
        if "zbl" in self.record.keys():
            eprint = {"eprint": self.record["zbl"], "eprinttype": "zbl"}
        elif "arxiv" in self.record.keys():
            eprint = {"eprint": self.record["arxiv"], "eprinttype": "arxiv"}
        else:
            eprint = {}

        captured = ("journal", "volume", "number", "pages", "year", "title", "doi")
        record_captured = {k: v for k, v in self.record.items() if k in captured}

        id_candidates = ("zbl", "arxiv", "doi", "issn", "title")
        key, identifier = [
            (key, self.record.get(key))
            for key in id_candidates
            if self.record.get(key) is not None
        ][0]
        record_special = {
            "ID": f"{key}:{identifier}",
            "ENTRYTYPE": self.record["bibtype"],
        }
        if "authors" in self.record.keys():
            record_special["author"] = " and ".join(self.record["authors"])

        try:
            bibtex = tomllib.loads(
                (self.local_record_folder / key / f"{identifier}.toml").read_text()
            )
        except FileNotFoundError:
            bibtex = self.bibtex

        return {**eprint, **record_captured, **record_special, **bibtex}

    def as_tuple(self) -> tuple[str, str, str | None, str | None, str | None, bool]:
        bibtex_record = self.as_bibtex()
        return (
            bibtex_record["eprinttype"],
            bibtex_record["eprint"],
            bibtex_record.get("title"),
            bibtex_record.get("author"),
            bibtex_record.get("year"),
            (
                xdg_data_home()
                / "mathbib"
                / "files"
                / "zbl"
                / f"{bibtex_record['eprint']}.pdf"
            ).exists(),
        )

    def __str__(self) -> str:
        key, id, title, author, year, exists = self.as_tuple()
        return f"{key}:{id} || {title} || {author} || {year} || file:{exists}"
