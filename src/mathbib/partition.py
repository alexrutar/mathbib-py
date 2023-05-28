from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

import json

from .remote import KeyId


class Partition:
    """This is a class which defines a partition of a set of objects.
    The objects must be sortable."""

    def __init__(self):
        self._dict: dict[KeyId, list[KeyId]] = {}
        self._lookup: dict[KeyId, KeyId] = {}

    def canonical(self, elem: KeyId) -> KeyId:
        """Get the canonical record associated with an element."""
        return self._lookup[elem]

    def iter_canonical(self) -> Iterable[KeyId]:
        return iter(self._dict.keys())

    def related(self, elem: KeyId) -> list[KeyId]:
        """Get the canonical record associated with an element."""
        return self._dict[self._lookup[elem]]

    def add(self, *elements: KeyId):
        """Add all possible new relations between elements."""

        if len(elements) > 0:
            # all possible canonical elements
            canonicals = [
                self._lookup[rel] for rel in elements if rel in self._lookup.keys()
            ]

            # remote all the elements from the dict, and build a large combined entry
            existing = {
                elem
                for canon in canonicals
                if canon in self._dict.keys()
                for elem in self._dict.pop(canon)
            }
            existing.update(elements)

            # add the new elements to the combined entry
            combined = sorted(existing)
            canon = combined[0]

            # add the new partition element
            self._dict[canon] = combined

            # add the lookups
            self._lookup.update({elem: canon for elem in combined})

    def serialize(self) -> str:
        serializable = {
            "records": {
                str(k): [str(elem) for elem in v] for k, v in self._dict.items()
            },
            "lookup": {str(k): str(v) for k, v in self._lookup.items()},
        }
        return json.dumps(serializable)

    @classmethod
    def from_serialized(cls, serialized: str):
        self = cls()
        record = json.loads(serialized)
        partition_dict = {
            KeyId._from_str_no_check(k): [KeyId._from_str_no_check(elem) for elem in v]
            for k, v in record["records"].items()
        }
        lookup = {
            KeyId._from_str_no_check(k): KeyId._from_str_no_check(v)
            for k, v in record["lookup"].items()
        }
        self._dict = partition_dict
        self._lookup = lookup
        return self

    def __getitem__(self, elem: KeyId) -> list[KeyId]:
        return self._dict[self._lookup[elem]]

    def __contains__(self, elem: KeyId):
        return elem in self._lookup.keys()

    def __str__(self):
        return str(list(self._dict.values()))
