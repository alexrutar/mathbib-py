import urllib.request
import re
from pathlib import Path
from nameparser import HumanName

import tomllib

from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from remote import arxiv_remote, zbmath_remote, zbl_remote

from xdg_base_dirs import xdg_data_home


def zbmath_search(query: str) -> str | None:
    with urllib.request.urlopen(f"https://zbmath.org/?q={query}") as fp:
        result = fp.read().decode("utf8")

    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)


def zbmath_search_doi(doi: str) -> str | None:
    return zbmath_search("en:" + doi)


# a record should be a dict, with priority (1) arxiv, (2) zbl, (3) local record
# there should be a distinct internal dict for each (all with the same keys)
# outputting the record should throw the keys from the highest priority dictf
class ArchiveRecord:
    def __init__(self, remote_record=None):
        self.record = remote_record if remote_record is not None else {}
        self.bibtex = self.record.pop("bibtex", {})
        self.record["authors"] = self.canonicalize_authors(self.record["authors"])

    @staticmethod
    def canonicalize_authors(author_list: list[str]):
        human_names = (HumanName(author) for author in author_list)
        return [f"{hn.last}, {hn.first} {hn.middle}".strip() for hn in human_names]

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
            raise ValueError("Could not find DOI.")

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
            "author": " and ".join(self.record["authors"]),
        }

        try:
            bibtex = tomllib.loads(
                (xdg_data_home() / "mathbib" / key / f"{identifier}.toml").read_text()
            )
        except FileNotFoundError:
            bibtex = self.bibtex

        return {**eprint, **record_captured, **record_special, **bibtex}


def cite_file_search(path: Path) -> list[ArchiveRecord]:
    cmds = set(
        re.findall(
            r"\\(?:|paren|foot|text|super|auto)cite{(arxiv|zbl):([\d\.]+)}",
            path.read_text(),
        )
    )
    method_table = {
        "arxiv": ArchiveRecord.from_arxiv,
        "zbl": ArchiveRecord.from_zbl,
    }
    return [method_table[key](index) for key, index in cmds]


def generate_file_citations(*paths: Path) -> str:
    db = BibDatabase()
    db.entries = [
        record.as_bibtex() for path in paths for record in cite_file_search(path)
    ]

    writer = BibTexWriter()
    writer.indent = "  "
    return writer.write(db)
