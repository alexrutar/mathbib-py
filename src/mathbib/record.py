from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, TypedDict

    class RecordEntry(TypedDict):
        id: str
        record: dict

    RecordList = dict[str, RecordEntry]

from itertools import chain
import operator
from functools import reduce
import tomllib

from xdg_base_dirs import xdg_data_home

from .external import REMOTES, parse_key_id, key_order


def get_records(
    keyid_pairs: Iterable[tuple[str, str]]
) -> dict[tuple[str, str], tuple[dict, dict[str, str]]]:
    return {
        (key, identifier): REMOTES[key].load_record(identifier)
        for key, identifier in keyid_pairs
    }


def extract_keyid_pairs(
    to_resolve: Iterable[tuple[dict, dict[str, str]]]
) -> dict[str, str]:
    return {k: v for _, dct in to_resolve for k, v in dct.items()}


def _resolve_all_records(
    keyid_pairs: Iterable[tuple[str, str]], resolved: set[str]
) -> Iterable[tuple[str, str, dict]]:
    results = get_records(
        ((key, identifier) for key, identifier in keyid_pairs if key not in resolved)
    )
    yield from (
        (key, identifier, rec) for ((key, identifier), (rec, _)) in results.items()
    )

    resolved.update(k for k, _ in keyid_pairs)
    to_resolve = extract_keyid_pairs(results.values())

    if len(to_resolve) > 0:
        yield from _resolve_all_records(to_resolve.items(), resolved)


def resolve_records(start_key: str, start_identifier: str) -> RecordList:
    def _sort_order(trip: tuple[str, str, dict]) -> int:
        key, _, _ = trip
        return key_order(key)

    return {
        key: {"id": identifier, "record": record}
        for key, identifier, record in sorted(
            _resolve_all_records(((start_key, start_identifier),), set()),
            key=_sort_order,
        )
    }


def merge_records(record_list: RecordList) -> dict:
    records = (rec["record"] for rec in record_list.values())

    returned_record = reduce(operator.ior, records, {})
    returned_record["classifications"] = sorted(
        chain.from_iterable(rec.get("classifications", []) for rec in records)
    )
    return returned_record


class ArchiveRecord:
    def __init__(self, keyid: str):
        self.key, self.identifier = parse_key_id(keyid)
        self.record = merge_records(resolve_records(self.key, self.identifier))

        # TODO: do not hardcode
        self.local_record_folder = xdg_data_home() / "mathbib" / "records"

    def as_bibtex(self) -> dict:
        eprint = {"eprint": self.identifier, "eprinttype": self.key}

        captured = ("journal", "volume", "number", "pages", "year", "title")
        captured = {k: v for k, v in self.record.items() if k in captured}

        special = {
            "ID": f"{self.key}:{self.identifier}",
            "ENTRYTYPE": self.record["bibtype"],
        }
        if "authors" in self.record.keys():
            special["author"] = " and ".join(self.record["authors"])

        try:
            # TODO: something more intelligent?
            bibtex = tomllib.loads(
                (
                    self.local_record_folder / self.key / f"{self.identifier}.toml"
                ).read_text()
            )
        except FileNotFoundError:
            bibtex = {}

        return {**eprint, **captured, **special, **bibtex}

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
