from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Iterable, Callable
    from ..request import RemoteSession
    from . import ParsedRecord, KeyId

from importlib.resources import files
import re
from urllib.parse import quote
import json

from nameparser import HumanName

from ..bibtex import BibTexHandler, CAPTURED
from .error import RemoteParseError
from .. import resources


class RelatedRecord:
    def __init__(
        self,
        related_key: str,
        related_identifier: str
        | tuple[Callable[[str], str], Callable[[str], Optional[str]]],
    ):
        """source_key: the starting point of the relation
        related_key: the ending point of the relation
        """
        self.related_key = related_key
        self.related_identifier = related_identifier

    def resolve(
        self, source_key: KeyId, session: RemoteSession
    ) -> Optional[tuple[str, str]]:
        """In order to resolve, we need a RemoteSession instance in order to make
        the remote request, and also a source KeyId
        """
        if isinstance(self.related_identifier, str):
            return self.related_key, self.related_identifier
        else:
            url_builder, parser = self.related_identifier
            response, _ = session.make_request(source_key, url_builder)
            if response is not None:
                parsed = parser(response)
                if parsed is not None:
                    return self.related_key, parsed
        return None


def zbmath_external_identifier_url(identifier: str) -> str:
    return f"https://zbmath.org/?q=en:{quote(identifier)}"


def zbmath_external_identifier_parse(result: str) -> Optional[str]:
    search_result = re.search(r"Zbl ([\d\.]+)", result)
    if search_result is not None:
        return search_result.group(1)
    return None


def parse_journal(journal: str, fjournal: Optional[str] = None):
    journal_abbrevs = json.loads(
        files(resources).joinpath("journal_abbrevs.json").read_text()
    )

    def normalize(name: str) -> str:
        return name.lower().replace(" ", "_").replace(".", "")

    if fjournal is not None:
        abbrev = journal_abbrevs.get(normalize(fjournal))

    else:
        abbrev = journal_abbrevs.get(normalize(journal))

    if abbrev is not None:
        return abbrev
    else:
        return journal


def canonicalize_authors(author_list: Iterable[str]) -> list[str]:
    human_names = [HumanName(author) for author in author_list]
    for hn in human_names:
        hn.capitalize()
    return [f"{hn.last}, {hn.first} {hn.middle}".strip() for hn in human_names]


def parse_bibtex(result: str) -> ParsedRecord:
    bibtex_parsed = BibTexHandler().loads(result).entries[0]

    # drop some keys from the bibtex file
    dropped = (
        "title",
        "url",
        "month",
        "journal",
        "fjournal",
        "ENTRYTYPE",
        "ID",
        "zbl",
        "keywords",
        "author",
        "zbmath",
        "doi",
        "isbn",
        "issn",
    )

    related = (
        "zbmath",
        "doi",
        "zbl",
    )

    # TODO: also get ISBN or ISSN?
    # TODO: since there could be multiple associated ISBN records, the 'related' field
    # needs to be refactored to be a list of KeyId

    extracted = {k: v for k, v in bibtex_parsed.items() if k in CAPTURED}
    try:
        additional = {
            # save any bibtex keys not captured or dropped
            "bibtex": {
                k: v
                for k, v in bibtex_parsed.items()
                if k not in CAPTURED and k not in dropped
            },
            "bibtype": bibtex_parsed["ENTRYTYPE"],
        }
    except KeyError:
        raise RemoteParseError("BibLaTeX file missing essential key 'ENTRYTYPE'")

    if "author" in bibtex_parsed.keys():
        additional["authors"] = canonicalize_authors(bibtex_parsed["author"])

    if "journal" in bibtex_parsed.keys():
        additional["journal"] = parse_journal(
            bibtex_parsed["journal"], fjournal=bibtex_parsed.get("fjournal")
        )

    return {**extracted, **additional}, [
        RelatedRecord(k, v) for k, v in bibtex_parsed.items() if k in related
    ]
