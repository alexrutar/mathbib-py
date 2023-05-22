from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Container, Optional
    from pathlib import Path

from urllib.request import urlopen
from urllib.parse import quote
import re

from bs4 import BeautifulSoup

from typing import Iterable

import bibtexparser as bp
from bibtexparser.bparser import BibTexParser
from nameparser import HumanName


def zbmath_search(query: str) -> str | None:
    with urlopen(f"https://zbmath.org/?q={quote(query)}") as fp:
        result = fp.read().decode("utf8")

    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)


def make_zbmath_query(title: str, authors: Iterable[str]):
    return f'ti:{title} & au:{" ".join(authors)}'


def arxiv_search(query: str) -> str | None:
    # return f"https://export.arxiv.org/api/query?id_list={arxiv}"
    print(
        f"https://export.arxiv.org/api/query?search_query={quote(query)}&max_results=1"
    )
    with urlopen(
        f"https://export.arxiv.org/api/query?search_query={quote(query)}&max_results=1"
    ) as fp:
        result = fp.read().decode("utf8")
    meta = BeautifulSoup(result, features="xml")
    if meta.entry is not None:
        print(meta.entry.id)


def make_arxiv_query(title: str, authors: Iterable[str]):
    author_merged = " AND ".join(f"au:{auth}" for auth in authors)
    return f"ti:{title} AND {author_merged}"


def search_authtitle(title: str, authors: Iterable[str]) -> Optional[str]:
    print(title, authors)
    zb_result = zbmath_search(make_zbmath_query(title, authors))
    if zb_result:
        return "zbl:" + zb_result
    else:
        arxiv_result = arxiv_search(make_arxiv_query(title, authors))
        if arxiv_result:
            return "arxiv:" + arxiv_result


def zbmath_search_bib(bibfile: Path):
    db = get_bib(bibfile)

    results = {
        entry["ID"]: search_authtitle(
            entry.get("title"),
            tuple(HumanName(auth).last for auth in entry.get("author")),
        )
        for entry in db.entries
    }

    return {k: v for k, v in results.items() if v is not None}


def get_bib(bibfile: Path, keys: Optional[Container] = None):
    parser = BibTexParser(common_strings=False)
    parser.ignore_nonstandard_types = False

    def customizations(record):
        return bp.customization.convert_to_unicode(
            bp.customization.page_double_hyphen(bp.customization.author(record))
        )

    parser.customization = customizations

    db = bp.loads(bibfile.read_text(), parser)
    if keys:
        db.entries = [entry for entry in db.entries if entry["ID"] in keys]
    return db


def zbmath_search_doi(doi: str) -> str | None:
    return zbmath_search("en:" + doi)
