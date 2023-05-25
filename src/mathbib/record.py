from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, TypedDict, Sequence, Optional

    class RecordEntry(TypedDict):
        id: str
        record: dict

    RecordList = dict[str, RecordEntry]

from itertools import chain
import operator
import json
from functools import reduce

from xdg_base_dirs import xdg_data_home

from .remote import KeyId, AliasedKeyId
from .request import load_record, NullRecordError
from .bibtex import CAPTURED
from .term import TermWrite


def _get_record_lists(
    keyid_pairs: Iterable[KeyId],
) -> dict[KeyId, tuple[Optional[dict], dict[str, str]]]:
    return {keyid: load_record(keyid) for keyid in keyid_pairs}


def _extract_keyid_pairs(
    to_resolve: Iterable[tuple[Optional[dict], dict[str, str]]]
) -> Sequence[KeyId]:
    return [
        KeyId.from_str(f"{key}:{identifier}")
        for _, related in to_resolve
        for key, identifier in related.items()
    ]


def _resolve_all_records(
    keyid_pairs: Iterable[KeyId], resolved: set[KeyId]
) -> Iterable[tuple[KeyId, dict]]:
    results = _get_record_lists(
        (keyid for keyid in keyid_pairs if keyid not in resolved)
    )
    yield from ((keyid, rec) for keyid, (rec, _) in results.items() if rec is not None)

    resolved.update(keyid_pairs)
    to_resolve = _extract_keyid_pairs(results.values())

    if len(to_resolve) > 0:
        yield from _resolve_all_records(to_resolve, resolved)


def _get_record_dict(start_keyid: KeyId) -> dict[KeyId, dict]:
    return dict(sorted(_resolve_all_records((start_keyid,), set())))


class ArchiveRecord:
    def __init__(self, keyid: AliasedKeyId):
        self.keyid = keyid
        self.record = _get_record_dict(keyid.drop_alias())

    def __hash__(self) -> int:
        return hash(self.keyid)

    @classmethod
    def from_str(cls, keyid_str: str, alias: Optional[str] = None):
        return cls(AliasedKeyId.from_str(keyid_str, alias=alias))

    def as_json(self) -> str:
        return json.dumps({str(k): v for k, v in self.record.items()})

    def as_joint_record(self) -> dict:
        records = list(reversed(self.record.values()))
        returned_record = reduce(operator.ior, records, {})

        # collect compound keys
        classifications = sorted(
            set(chain.from_iterable(rec.get("classifications", []) for rec in records))
        )
        if len(classifications) > 0:
            returned_record["classifications"] = classifications

        bibtex = reduce(operator.ior, (rec.get("bibtex", {}) for rec in records), {})
        if len(bibtex) > 0:
            returned_record["bibtex"] = bibtex

        return returned_record

    def related_keys(self) -> Iterable[KeyId]:
        return self.record.keys()

    def priority_key(self) -> KeyId:
        try:
            return next(iter(self.record.keys()))
        except StopIteration:
            raise NullRecordError(self.keyid)

    def is_null(self, warn: bool = False) -> bool:
        ret = len(self.as_joint_record()) == 0
        if warn and ret:
            TermWrite.warn(f"Null record '{self.keyid}'")
        return ret

    def get_local_bibtex(self) -> dict:
        return reduce(
            operator.ior,
            (keyid.toml_record() for keyid in reversed(self.record.keys())),
            {},
        )

    def as_bibtex(self) -> dict:
        joint_record = self.as_joint_record()

        eprint_keyid = self.priority_key()
        eprint = {
            "eprint": eprint_keyid.identifier,
            "eprinttype": str(eprint_keyid.key),
        }

        captured = {k: v for k, v in joint_record.items() if k in CAPTURED}

        special = {
            "ID": str(self.keyid) if self.keyid.alias is None else self.keyid.alias,
            "ENTRYTYPE": joint_record["bibtype"],
        }
        if "authors" in joint_record.keys():
            special["author"] = " and ".join(joint_record["authors"])

        return {**eprint, **captured, **special, **self.get_local_bibtex()}

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
