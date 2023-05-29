from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Final, Optional
    from .record import ArchiveRecord

import bibtexparser as bp
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.customization import convert_to_unicode, page_double_hyphen, author


CAPTURED: Final = (
    "language",
    "number",
    "pages",
    "publisher",
    "title",
    "volume",
    "year",
    "journal",
    "booktitle",
)


class BibTexHandler:
    def __init__(self):
        self.writer = BibTexWriter()
        self.writer.indent = "  "

        self.parser = BibTexParser()
        self.parser.customization = lambda record: convert_to_unicode(
            page_double_hyphen(author(record))
        )
        self.parser.ignore_nonstandard_types = False

    def loads(self, bibstr: str) -> BibDatabase:
        return bp.loads(bibstr, self.parser)

    def write_records(self, records: Iterable[Optional[ArchiveRecord]]) -> str:
        db = BibDatabase()
        db.entries = [
            record.as_bibtex()
            for record in records
            if record is not None and not record.is_null(warn=True)
        ]
        return self.dumps(db)

    def dumps(self, db: BibDatabase) -> str:
        return self.writer.write(db)
