import urllib.request
from bs4 import BeautifulSoup
# import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode, page_double_hyphen, author
from bibtexparser import loads
import re
from pathlib import Path
from dataclasses import dataclass
from nameparser import HumanName


def cite_file_search(path: Path):
    cmds = re.findall(
        r"\\(?:|paren|foot|text|super|auto)cite{(arx|zbl|mr):([\d\.]+)}",
        path.read_text(),
    )
    method_table = {"arx": BaseRecord.from_arxiv, "zbl": BaseRecord.from_zbl}
    return [method_table[key](index) for key, index in cmds]


class ZBmath:
    @staticmethod
    def search(query: str) -> str | None:
        with urllib.request.urlopen(f"https://zbmath.org/?q={query}") as fp:
            result = fp.read().decode("utf8")

        title = BeautifulSoup(result, "html.parser").title
        if title is not None:
            title_string = title.string
            if title_string is not None:
                return title_string.split(" ")[2]

    @staticmethod
    def search_doi(doi: str) -> str | None:
        return ZBmath.search("en:" + doi)

    @staticmethod
    def get_bib(zbl: str) -> str | None:
        with urllib.request.urlopen(f"https://zbmath.org/bibtex/{zbl}.bib") as fp:
            result = fp.read().decode("utf8")
        return result

    @staticmethod
    def get_metadata(zbmath: str):
        with urllib.request.urlopen(
            f"https://oai.zbmath.org/v1/?verb=GetRecord&identifier=oai:zbmath.org:{zbmath}&metadataPrefix=oai_zb_preview"
        ) as fp:
            result = fp.read().decode("utf8")

        metadata = BeautifulSoup(result, features="xml")

        return {
            "author_ids": [
                entry.string for entry in metadata.find_all("zbmath:author_id")
            ],
            "classifications": [
                entry.string for entry in metadata.find_all("zbmath:classification")
            ],
            "title": metadata.find_all("zbmath:document_title")[0].string,
        }


class ArXiV:
    @staticmethod
    def parse_classifications(class_list):
        return re.findall(r"(math\.[A-Z][A-Z]|\d\d[A-Z]\d\d)", " ".join(class_list))

    @staticmethod
    def get_metadata(arxiv: str):
        with urllib.request.urlopen(
            f"https://export.arxiv.org/api/query?id_list={arxiv}"
        ) as fp:
            result = fp.read().decode("utf8")

        metadata = BeautifulSoup(result, features="xml").entry
        return {
            "authors": [HumanName(entry.string) for entry in metadata.find_all("name")],
            "title": " ".join(metadata.find_all("title")[0].string.split()),
            "classifications": ArXiV.parse_classifications(
                entry["term"] for entry in metadata.find_all("category")
            ),
        }


@dataclass
class BaseRecord:
    arxiv: str | None = None
    authors: list[HumanName] | None = None
    author_ids: list[str] | None = None
    bibtype: str = "preprint"
    classifications: str | None = None
    doi: str | None = None
    journal: str | None = None
    journal_full: str | None = None
    number: str| None = None
    pages: str| None = None
    title: str | None = None
    url: str | None = None
    volume: str| None = None
    year: str| None = None
    zbl: str | None = None
    zbmath: str | None = None

    @classmethod
    def from_arxiv(cls, arxiv: str):
        meta = ArXiV.get_metadata(arxiv)
        return cls(
            arxiv=arxiv,
            authors=meta["authors"],
            bibtype="article",
            classifications=meta["classifications"],
            title=meta["title"],
            url="https://arxiv.org/abs/{arxiv}",
        )

    @classmethod
    def from_zbl(cls, zbl: str):
        # TODO: proper error if fails
        bibtex = ZBmath.get_bib(zbl)

        parser = BibTexParser()
        def customizations(record):
            record = convert_to_unicode(record)
            record = page_double_hyphen(record)
            record = author(record)
            return record
        parser.customization = customizations

        bibtex_parsed = loads(bibtex, parser=parser).entries[0]

        zbmath = bibtex_parsed["zbmath"]
        meta = ZBmath.get_metadata(zbmath)

        if (
            meta["title"]
            == "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
        ):
            title = bibtex_parsed.get("title")
        else:
            title = meta.get("title")

        return cls(
            authors=[
                HumanName(author) for author in bibtex_parsed["author"]
            ],
            author_ids=meta["author_ids"],
            bibtype="article",
            classifications=meta["classifications"],
            doi=bibtex_parsed.get("doi"),
            journal=bibtex_parsed.get("journal"),
            journal_full=bibtex_parsed.get("fjournal"),
            number=bibtex_parsed.get("number"),
            pages=bibtex_parsed.get("pages"),
            title=title,
            url=f"https://zbmath.org/{zbl}",
            volume=bibtex_parsed.get("volume"),
            year=bibtex_parsed.get("year"),
            zbl=zbl,
            zbmath=zbmath,
        )

    @classmethod
    def from_doi(cls, doi: str):
        res = ZBmath.search_doi(doi)
        if res is not None:
            return cls.from_zbl(res)
        else:
            # TODO: better error
            raise ValueError("Could not find record associated with DOI!")


# a record should be a dict, with priority (1) arxiv, (2) zbl, (3) manual entry
# there should be a distinct internal dict for each (all with the same keys)
# outputting the record should throw the keys from the highest priority dictf
class ArchiveRecord:
    def __init__(self, zbl: str | None = None, arxiv: str | None = None):
        self.url = f"https://zbmath.org/{zbl}"
        self.arxiv = arxiv
        self.zbl = zbl
        if self.arxiv is not None:
            pass
        if self.zbl is not None:
            self.bibtex = ZBmath.get_bib(self.zbl)

            bibtex_parsed = bibtexparser.loads(self.bibtex).entries[0]
            self.zbmath = bibtex_parsed["zbmath"]

            meta = ZBmath.get_metadata(self.zbmath)

            self.authors = meta["authors"]
            self.classifications = meta["classifications"]
            if (
                meta["title"]
                == "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
            ):
                self.title = bibtex_parsed["title"]
            else:
                self.title = meta["title"]

            self.journal = bibtex_parsed["journal"]
            self.journal_full = bibtex_parsed["fjournal"]
            self.doi = bibtex_parsed["doi"]

    @classmethod
    def from_doi(cls, doi: str):
        res = ZBmath.search_doi(doi)
        if res is not None:
            return cls(res)
        else:
            # TODO: better error
            raise ValueError("Could not find record associated with DOI!")

    def __repr__(self):
        return str(self.__dict__)
