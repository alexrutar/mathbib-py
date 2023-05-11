from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

from ..remote import RemoteRecord
from . import arxiv
from . import zbl
from . import zbmath


arxiv_remote: Final = RemoteRecord("arxiv", arxiv.url_builder, arxiv.record_parser)
zbl_remote: Final = RemoteRecord("zbl", zbl.url_builder, zbl.record_parser)
zbmath_remote: Final = RemoteRecord("zbmath", zbmath.url_builder, zbmath.record_parser)
