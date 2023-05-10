from datetime import datetime
import re

from bs4 import BeautifulSoup


def url_builder(arxiv: str) -> str:
    return f"https://export.arxiv.org/api/query?id_list={arxiv}"


def record_parser(result: str) -> dict:
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