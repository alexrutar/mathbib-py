from nameparser import HumanName

import tomllib

from .api import arxiv_remote, zbmath_remote, zbl_remote
from .search import zbmath_search_doi
from .error import RemoteAccessError

from xdg_base_dirs import xdg_data_home


def _canonicalize_authors(author_list: list[str]):
    human_names = (HumanName(author) for author in author_list)
    return [f"{hn.last}, {hn.first} {hn.middle}".strip() for hn in human_names]


class ArchiveRecord:
    def __init__(self, remote_record=None):
        self.record = remote_record if remote_record is not None else {}
        self.bibtex = self.record.pop("bibtex", {})
        if "authors" in self.record.keys():
            self.record["authors"] = _canonicalize_authors(self.record["authors"])

        self.local_record_folder = xdg_data_home() / "mathbib" / "records"

    @classmethod
    def from_arxiv(cls, arxiv: str):
        return cls(remote_record=arxiv_remote.load_record(arxiv))

    @classmethod
    def from_zbl(cls, zbl: str):
        zbl_record = zbl_remote.load_record(zbl)
        zbmath_record = zbmath_remote.load_record(zbl_record["zbmath"])
        if "arxiv" in zbmath_record.keys():
            arxiv_record = arxiv_remote.load_record(zbmath_record["arxiv"])
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

        captured = ("journal", "number", "pages", "year", "title")
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
