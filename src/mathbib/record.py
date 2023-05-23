from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, TypedDict, Sequence

    class RecordEntry(TypedDict):
        id: str
        record: dict

    RecordList = dict[str, RecordEntry]

from itertools import chain
import operator
import json
from functools import reduce
import tomllib

from xdg_base_dirs import xdg_data_home

from .external import REMOTES, KeyId


def get_record_lists(
    keyid_pairs: Iterable[KeyId],
) -> dict[KeyId, tuple[dict, dict[str, str]]]:
    return {
        keyid: REMOTES[keyid.key].load_record(keyid.identifier) for keyid in keyid_pairs
    }


def extract_keyid_pairs(
    to_resolve: Iterable[tuple[dict, dict[str, str]]]
) -> Sequence[KeyId]:
    return [
        KeyId.from_keyid(f"{key}:{identifier}")
        for _, related in to_resolve
        for key, identifier in related.items()
    ]


def _resolve_all_records(
    keyid_pairs: Iterable[KeyId], resolved: set[KeyId]
) -> Iterable[tuple[KeyId, dict]]:
    results = get_record_lists(
        (keyid for keyid in keyid_pairs if keyid not in resolved)
    )
    yield from ((keyid, rec) for keyid, (rec, _) in results.items())

    resolved.update(keyid_pairs)
    to_resolve = extract_keyid_pairs(results.values())

    if len(to_resolve) > 0:
        yield from _resolve_all_records(to_resolve, resolved)


def get_record_list(start_keyid: KeyId) -> dict[KeyId, dict]:
    return dict(sorted(_resolve_all_records((start_keyid,), set())))


def _merge_records(record_list: dict[KeyId, dict]) -> dict:
    # reverse order, since reduce will prioritize later keys rather than earlier
    records = reversed(list(record_list.values()))
    returned_record = reduce(operator.ior, records, {})

    returned_record["classifications"] = sorted(
        set(chain.from_iterable(rec.get("classifications", []) for rec in records))
    )
    return returned_record


def get_joint_record(keyid: KeyId) -> dict:
    return _merge_records(get_record_list(keyid))


class ArchiveRecord:
    def __init__(self, keyid: KeyId):
        self.keyid = keyid
        self.record = get_record_list(keyid)

        # TODO: do not hardcode
        self.local_record_folder = xdg_data_home() / "mathbib" / "records"

    @classmethod
    def from_keyid(cls, keyid: str):
        return cls(KeyId.from_keyid(keyid))

    def as_json(self) -> str:
        return json.dumps({str(k): v for k, v in self.record.items()})

    def as_joint_record(self) -> dict:
        records = reversed(list(self.record.values()))
        returned_record = reduce(operator.ior, records, {})

        returned_record["classifications"] = sorted(
            set(chain.from_iterable(rec.get("classifications", []) for rec in records))
        )
        return returned_record

    def related_keys(self) -> Iterable[KeyId]:
        return self.record.keys()

    def priority_key(self) -> KeyId:
        return next(iter(self.record.keys()))

    def as_bibtex(self) -> dict:
        joint_record = self.as_joint_record()

        eprint = {"eprint": self.keyid.identifier, "eprinttype": str(self.keyid.key)}

        captured = ("journal", "volume", "number", "pages", "year", "title")
        captured = {k: v for k, v in joint_record.items() if k in captured}

        special = {
            "ID": f"{self.keyid.key}:{self.keyid.identifier}",
            "ENTRYTYPE": joint_record["bibtype"],
        }
        if "authors" in joint_record.keys():
            special["author"] = " and ".join(joint_record["authors"])

        try:
            # TODO: something more intelligent?
            bibtex = tomllib.loads(self.keyid.toml_path().read_text())

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
