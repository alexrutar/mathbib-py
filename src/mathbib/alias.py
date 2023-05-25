from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .remote import AliasedKeyId
    from pathlib import Path

from xdg_base_dirs import xdg_data_home
from tomllib import loads, TOMLDecodeError
import sys

from tomli_w import dumps

from .request import load_record
from .term import TermWrite


def alias_path(mkdir: bool = False) -> Path:
    aliasp = xdg_data_home() / "mathbib" / "alias.toml"
    if mkdir:
        aliasp.parent.mkdir(exist_ok=True, parents=True)
    return aliasp


def load_alias_dict(sys_fail: bool = False) -> dict[str, str]:
    try:
        return loads(alias_path().read_text())
    except TOMLDecodeError as e:
        if sys_fail:
            TermWrite.error(f"Malformed alias file at '{alias_path()}'")
            sys.exit(1)
        else:
            raise e


def add_bib_alias(alias: str, aliased_keyid: AliasedKeyId):
    keyid = aliased_keyid.drop_alias()
    record, _ = load_record(keyid)
    if record is None:
        TermWrite.error(f"Null record associated with '{keyid}'")
        sys.exit(1)

    try:
        alias_dict = load_alias_dict(sys_fail=True)
    except FileNotFoundError:
        alias_dict = {}
    alias_dict[alias] = str(keyid)
    alias_path(mkdir=True).write_text(dumps(alias_dict))


def delete_bib_alias(alias: str):
    aliasp = alias_path()
    try:
        alias_dict = load_alias_dict(sys_fail=True)
        del alias_dict[alias]
        aliasp.write_text(dumps(alias_dict))

    except (FileNotFoundError, KeyError):
        TermWrite.error(f"No alias with name '{alias}'")
        sys.exit(1)


def get_bib_alias(alias: str) -> str:
    try:
        alias_dict = load_alias_dict(sys_fail=True)
        return alias_dict[alias]

    except (FileNotFoundError, KeyError):
        TermWrite.error(f"No alias with name '{alias}'")
        sys.exit(1)
