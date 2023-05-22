from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Container
    from pathlib import Path

from urllib.request import urlopen
from urllib.parse import quote
import re

from typing import Iterable

import bibtexparser as bp
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from nameparser import HumanName


def zbmath_search(query: str) -> str | None:
    with urlopen(f"https://zbmath.org/?q={quote(query)}") as fp:
        result = fp.read().decode("utf8")

    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)

def make_zbmath_query(title: str, authors: Iterable[str]):
    return f'ti:{title} & au:{" ".join(authors)}'

def zbmath_replace_bib(texfile: Path, bibfile: Path, keys: Container):
    db = get_subbib(bibfile, keys)

    searches = {entry['ID']: make_zbmath_query(entry.get('title'), tuple(HumanName(auth).last for auth in entry.get('author'))) for entry in db.entries}

    zbl_results_all = {key: zbmath_search(query) for key, query in searches.items()}
    zbl_results = {k: v for k,v in zbl_results_all.items() if v is not None}
    new_filecontents = re.sub("(" + "|".join(re.escape(k) for k in zbl_results.keys()) + ")", lambda s: f"zbl:{zbl_results.get(s.group(0))}", texfile.read_text())

    for entry in db.entries:
        candidate = zbl_results.get(entry["ID"])
        if candidate is not None:
            entry["ID"] = candidate

    return new_filecontents


def get_subbib(bibfile: Path, keys: Container):
    parser = BibTexParser(common_strings=False)
    parser.ignore_nonstandard_types = False

    def customizations(record):
        return bp.customization.convert_to_unicode(
            bp.customization.page_double_hyphen(bp.customization.author(record))
        )
    parser.customization = customizations

    db = bp.loads(bibfile.read_text(), parser)
    db.entries = [entry for entry in db.entries if entry["ID"] in keys]
    return db


def zbmath_search_doi(doi: str) -> str | None:
    return zbmath_search("en:" + doi)
