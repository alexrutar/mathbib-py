from urllib.request import urlopen
from urllib.parse import quote
import re


def zbmath_search(query: str) -> str | None:
    with urlopen(f"https://zbmath.org/?q={quote(query)}") as fp:
        result = fp.read().decode("utf8")

    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)


def zbmath_search_doi(doi: str) -> str | None:
    return zbmath_search("en:" + doi)
