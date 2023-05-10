from pathlib import Path
import re

from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from .record import ArchiveRecord


def cite_file_search(path: Path) -> list[ArchiveRecord]:
    """Open the file at `path`, parse for citation commands, and
    generate the corresponding list of ArchiveRecord,"""
    cmds = set(
        re.findall(
            r"\\(?:|paren|foot|text|super|auto)cite{(arxiv|zbl):([\d\.]+)}",
            path.read_text(),
        )
    )
    method_table = {
        "arxiv": ArchiveRecord.from_arxiv,
        "zbl": ArchiveRecord.from_zbl,
    }
    return [method_table[key](index) for key, index in cmds]


def generate_biblatex(*paths: Path) -> str:
    """Generate the biblatex file associated with the citations inside a given file."""
    db = BibDatabase()
    db.entries = [
        record.as_bibtex() for path in paths for record in cite_file_search(path)
    ]

    writer = BibTexWriter()
    writer.indent = "  "
    return writer.write(db)
