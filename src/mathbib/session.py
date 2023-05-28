from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, Type
    from types import TracebackType

from .alias import load_alias_dict
from .request import RemoteSession
from .partition import Partition

from xdg_base_dirs import xdg_data_home


class CLISession:
    def __init__(self, debug: bool, cache: bool, remote: bool):
        self.debug = debug
        self.cache = cache
        self.remote = remote
        self.relation_file = xdg_data_home() / "mathbib" / "relations.json"

    def __enter__(self):
        self.alias = load_alias_dict()
        self.remote_session = RemoteSession(cache=self.cache, remote=self.remote)
        try:
            self.relations = Partition.from_serialized(self.relation_file.read_text())
        except FileNotFoundError:
            self.relations = Partition()
        return self

    # TODO: properly catch errors here!
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ):
        self.relation_file.write_text(self.relations.serialize())
