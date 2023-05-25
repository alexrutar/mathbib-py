from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .external import KeyId
    from pathlib import Path

from xdg_base_dirs import xdg_data_home
from tomli_w import dumps
from tomllib import loads

from .external import load_record, NullRecordError


def alias_path(mkdir: bool = False) -> Path:
    aliasp = xdg_data_home() / "mathbib" / "alias.toml"
    if mkdir:
        aliasp.parent.mkdir(exist_ok=True, parents=True)
    return aliasp


def load_alias_dict() -> dict[str, str]:
    return loads(alias_path().read_text())


def add_bib_alias(alias: str, keyid: KeyId):
    record, _ = load_record(keyid)
    if record is None:
        raise NullRecordError(keyid)

    try:
        alias_dict = load_alias_dict()
    except FileNotFoundError:
        alias_dict = {}
    alias_dict[alias] = str(keyid)
    alias_path(mkdir=True).write_text(dumps(alias_dict))


def delete_bib_alias(alias: str):
    aliasp = alias_path()
    try:
        alias_dict = load_alias_dict()
        del alias_dict[alias]
        aliasp.write_text(dumps(alias_dict))

    except (FileNotFoundError, KeyError):
        raise KeyError(f"No alias record with name '{alias}'.")


def get_bib_alias(alias: str) -> str:
    try:
        alias_dict = load_alias_dict()
        return alias_dict[alias]

    except (FileNotFoundError, KeyError):
        raise KeyError(f"No alias record with name '{alias}'.")
