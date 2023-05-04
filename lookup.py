import urllib.request
from bs4 import BeautifulSoup
import bibtexparser

def zb_search(query: str) -> str | None:
    with urllib.request.urlopen(f"https://zbmath.org/?q={query}") as fp:
        result = fp.read().decode("utf8")

    title = BeautifulSoup(result, "html.parser").title
    if title is not None:
        title_string = title.string
        if title_string is not None:
            return title_string.split(" ")[2]


def zb_search_doi(doi: str) -> str | None:
    return zb_search("en:" + doi)


def zb_get_bib(zbl: str) -> str | None:
    with urllib.request.urlopen(f"https://zbmath.org/bibtex/{zbl}.bib") as fp:
        result = fp.read().decode("utf8")
    return result


def zb_get_metadata(zbmath: str):
    with urllib.request.urlopen(
        f"https://oai.zbmath.org/v1/?verb=GetRecord&identifier=oai:zbmath.org:{zbmath}&metadataPrefix=oai_zb_preview"
    ) as fp:
        result = fp.read().decode("utf8")

    metadata = BeautifulSoup(result, features="xml")

    return {
        "authors": [entry.string for entry in metadata.find_all("zbmath:author_id")],
        "classifications": [
            entry.string for entry in metadata.find_all("zbmath:classification")
        ],
        "title": metadata.find_all("zbmath:document_title")[0].string,
    }


def zb_get_metadata2(zbl: str):
    with urllib.request.urlopen(
        f"https://zbmath.org/{zbl}"
    ) as fp:
        result = fp.read().decode("utf8")

    metadata = BeautifulSoup(result)
    print(metadata)


class ZBRecord:
    def __init__(self, zbl: str):
        self.url = f"https://zbmath.org/{zbl}"
        self.zbl = zbl
        self.bibtex = zb_get_bib(zbl)

        bibtex_parsed = bibtexparser.loads(self.bibtex).entries[0]
        self.zbmath = bibtex_parsed['zbmath']

        meta = zb_get_metadata(self.zbmath)

        self.authors = meta['authors']
        self.classifications = meta['classifications']
        self.title = bibtex_parsed['title']
        self.journal = bibtex_parsed['journal']
        self.journal_full = bibtex_parsed['fjournal']
        self.doi = bibtex_parsed['doi']

    @classmethod
    def from_doi(cls, doi: str):
        res = zb_search_doi(doi)
        if res is not None:
            return cls(res)
        else:
            # TODO: better error
            raise ValueError("Could not find record associated with DOI!")


    def __repr__(self):
        return str(self.__dict__)


# print(zb_search_doi("10.1007/s00209-020-02546-0"))
# print(ZBRecord("1461.42012").title)
# print(ZBRecord.from_doi("10.54330/afm.120529"))
