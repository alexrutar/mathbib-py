from urllib.request import urlopen
from urllib.error import HTTPError
from typing import Callable, Final
from xdg_base_dirs import xdg_cache_home
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
import re

import bibtexparser as bp


class RemoteRecord:
    CACHE_DATE_FORMAT = f"%Y-%m-%dT%H:%M:%SZ"

    def __init__(
        self,
        key: str,
        url_builder: Callable[[str], str],
        record_parser: Callable[[str], dict],
        error_parser: Callable[[str], dict] | None = None,
    ):
        self.key = key
        self.cache_folder = xdg_cache_home() / "mathbib" / key
        self.url_builder = url_builder
        self.record_parser = record_parser
        self.error_parser = error_parser

    def load_cached_record(self, cache_file: Path) -> dict:
        return json.loads(cache_file.read_text())["record"]

    def get_cache_file(self, identifier: str) -> Path:
        """Get the cache file associated with the item identifier."""
        return self.cache_folder / f"{identifier}.json"

    def load_remote_record(self, identifier: str) -> dict:
        """Load and parse the remote record."""
        url = self.url_builder(identifier)
        try:
            with urlopen(url) as fp:
                return self.record_parser(fp.read().decode("utf8"))
        except HTTPError as e:
            print(f"Failed to access '{self.key}' identifier '{identifier}' at '{url}'")
            raise e

    def update_cached_record(self, identifier: str) -> None:
        """Forcibly update the cache from the remote record."""
        record = self.load_remote_record(identifier)
        self.serialize(identifier, record)

    def update_records(self, max_age: timedelta = timedelta(days=365)):
        """Update all records which are over a certain age."""
        for cache_file in self.cache_folder.glob("*.json"):
            cache_object = json.loads(cache_file.read_text())
            age = datetime.now() - datetime.strptime(
                cache_object["accessed"], self.CACHE_DATE_FORMAT
            )
            if age > max_age:
                self.update_cached_record(cache_file.stem)

    def load_record(self, identifier: str) -> dict:
        """Load the item identifier, defaulting to the cache if possible and writing to the cache after loading."""
        cache_file = self.get_cache_file(identifier)

        # attempt to load from cache
        try:
            record = self.load_cached_record(cache_file)

        except FileNotFoundError:
            record = self.load_remote_record(identifier)
            self.serialize(identifier, record)

        record[self.key] = identifier
        return record

    def serialize(self, identifier: str, record: dict) -> None:
        self.cache_folder.mkdir(parents=True, exist_ok=True)

        target = self.get_cache_file(identifier)
        cache_object = {
            "record": record,
            "accessed": datetime.now().strftime(self.CACHE_DATE_FORMAT),
        }
        target.write_text(json.dumps(cache_object))


def arxiv_url_builder(arxiv: str) -> str:
    return f"https://export.arxiv.org/api/query?id_list={arxiv}"


def arxiv_record_parser(result: str) -> dict:
    metadata = BeautifulSoup(result, features="xml").entry
    if metadata is None:
        raise ValueError("malformed arxiv")

    published = metadata.published
    if published is None:
        raise ValueError("malformed arxiv")
    date_str = published.string
    if date_str is None:
        raise ValueError("malformed arxiv")
    year = datetime.strptime(date_str, r"%Y-%m-%dT%H:%M:%SZ").strftime("%Y")

    arxiv_id = metadata.id
    if arxiv_id is None:
        raise ValueError("malformed arxiv")
    arxiv_link = arxiv_id.string
    if arxiv_link is None:
        raise ValueError("malformed arxiv")
    arxiv_id_search = re.fullmatch(
        r"https?://arxiv.org/abs/.+v([1-9][0-9]*)", arxiv_link
    )
    if arxiv_id_search is None:
        raise ValueError("malformed arxiv")

    classifications = sorted(
        re.findall(
            r"((?:math|stat|cs)\.[A-Z][A-Z]|\d\d[A-Z]\d\d)",
            " ".join(entry["term"] for entry in metadata.find_all("category")),
        )
    )

    return {
        "arxiv_version": int(arxiv_id_search.group(1)),
        "authors": [entry.string for entry in metadata.find_all("name")],
        "title": " ".join(metadata.find_all("title")[0].string.split()),
        "classifications": classifications,
        "year": year,
        "bibtype": "preprint",
    }


def zbmath_url_builder(zbmath: str) -> str:
    return f"https://oai.zbmath.org/v1/?verb=GetRecord&identifier=oai:zbmath.org:{zbmath}&metadataPrefix=oai_zb_preview"


def zbmath_record_parser(result: str) -> dict:
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
    if (
        candidate_title
        != "zbMATH Open Web Interface contents unavailable due to conflicting licenses."
    ):
        out["title"] = candidate_title

    return out


def zbl_url_builder(zbl: str) -> str:
    return f"https://zbmath.org/bibtex/{zbl}.bib"


def zbl_record_parser(result: str) -> dict:
    # parse bibtex string using bibtexparser
    parser = bp.bparser.BibTexParser()

    def customizations(record):
        return bp.customization.convert_to_unicode(
            bp.customization.page_double_hyphen(bp.customization.author(record))
        )

    parser.customization = customizations
    bibtex_parsed = bp.loads(result, parser=parser).entries[0]

    # capture some keys explicitly from the bibtex file
    captured = (
        "doi",
        "journal",
        "language",
        "issn",
        "number",
        "pages",
        "volume",
        "year",
        "zbmath",
    )

    # drop some keys from the bibtex file
    dropped = (
        "title",
        "fjournal",
        "zbmath",
        "ENTRYTYPE",
        "ID",
        "zbl",
        "keywords",
        "author",
    )

    extracted = {k: v for k, v in bibtex_parsed.items() if k in captured}
    additional = {
        # save any bibtex keys not captured or dropped
        "bibtex": {
            k: v
            for k, v in bibtex_parsed.items()
            if k not in captured and k not in dropped
        },
        "bibtype": bibtex_parsed["ENTRYTYPE"],
        "authors": bibtex_parsed["author"],
    }

    return {**extracted, **additional}


arxiv_remote: Final = RemoteRecord("arxiv", arxiv_url_builder, arxiv_record_parser)
zbmath_remote: Final = RemoteRecord("zbmath", zbmath_url_builder, zbmath_record_parser)
zbl_remote: Final = RemoteRecord("zbl", zbl_url_builder, zbl_record_parser)
