from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

import sqlite3 as sql3
from itertools import chain

from xdg_base_dirs import xdg_data_home, xdg_cache_home

from .record import ArchiveRecord


class IndexDatabase:
    def __init__(self):
        self.db_path = xdg_data_home() / "mathbib" / "index.db"
        self.keys = ("arxiv", "zbl")
        if not self.db_path.exists():
            con = sql3.connect(self.db_path)
            con.execute("CREATE TABLE records(key, id, title, author, year, file)")


def generate_records_from_storage():
    for path in (xdg_data_home() / "mathbib" / "files" / "zbl").glob("*.pdf"):
        print(ArchiveRecord.from_zbl(path.stem).as_tuple())

    for path in (xdg_data_home() / "mathbib" / "files" / "arxiv").glob("*.pdf"):
        print(ArchiveRecord.from_zbl(path.stem).as_tuple())

    for path in (xdg_data_home() / "mathbib" / "records" / "zbl").glob("*.toml"):
        print(ArchiveRecord.from_zbl(path.stem).as_tuple())

    for path in (xdg_data_home() / "mathbib" / "files" / "arxiv").glob("*.toml"):
        print(ArchiveRecord.from_zbl(path.stem).as_tuple())


def list_records() -> Iterable[ArchiveRecord]:
    zbl_records = (
        ArchiveRecord.from_zbl(path.stem)
        for path in (xdg_cache_home() / "mathbib" / "zbl").glob("*.json")
    )
    arxiv_records = (
        ArchiveRecord.from_arxiv(path.stem)
        for path in (xdg_cache_home() / "mathbib" / "arxiv").glob("*.json")
    )
    return chain(zbl_records, arxiv_records)
