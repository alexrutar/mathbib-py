from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bparser import BibTexParser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode, page_double_hyphen, author
import bibtexparser as bp

from typing import Final


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

    def write_dict(self, bibdict: dict) -> str:
        db = BibDatabase()
        db.entries = [bibdict]
        return self.dumps(db)

    def dumps(self, db: BibDatabase) -> str:
        return self.writer.write(db)


BIBTEX_HANDLER: Final = BibTexHandler()
