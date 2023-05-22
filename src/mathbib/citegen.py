from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Final

from itertools import chain
from pathlib import Path
import re

from .record import ArchiveRecord
from .bibtex import BibTexHandler

CITEKEY_REGEX: Final = re.compile(
    r"(?<!\\)%.+|(\\(?:|paren|foot|text|super|auto|no)citep?\{((?!\*)[^{}]+)\})"
)

SEARCHKEY_REGEX: Final = re.compile(r"((?:arxiv|doi|zbmath|zbl):(?:[\d\.]+))")

KEY_REGEX: Final = re.compile(r"([0-9a-zA-Z\.\-:_/]+)")


def get_citekeys(path: Path) -> Iterable[str]:
    cite_commands = (
        m.group(2) for m in CITEKEY_REGEX.finditer(path.read_text()) if m.group(2)
    )
    return set(chain.from_iterable(KEY_REGEX.findall(k) for k in cite_commands))


def cite_file_search(*paths: Path) -> Iterable[ArchiveRecord]:
    """Open the file at `path`, parse for citation commands, and
    generate the corresponding list of ArchiveRecord,"""

    # search for all citation commands
    cite_commands = chain.from_iterable(get_citekeys(path) for path in paths)

    # then parse each citation command to find a valid key
    cmds = set(chain.from_iterable(SEARCHKEY_REGEX.findall(k) for k in cite_commands))

    return (ArchiveRecord(keyid) for keyid in cmds)


def generate_biblatex(*paths: Path) -> str:
    """Generate the biblatex file associated with the citations inside a given file."""
    bth = BibTexHandler()
    return bth.write_records(cite_file_search(*paths))
