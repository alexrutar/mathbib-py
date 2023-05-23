from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Final, Sequence

from itertools import chain
from pathlib import Path
import re

from .record import ArchiveRecord
from .bibtex import BibTexHandler
from .external import KeyId
from .remote import RemoteKey


def find_identifiers(db_entry: dict) -> tuple[str, Sequence[KeyId]]:
    # TODO: also get ISBN, but needs validation
    identifiers = [
        KeyId.from_keyid(f"{k}:{v}")
        for k, v in db_entry.items()
        if k in ("doi", "arxiv", "zbl", "isbn")
    ]
    eprint = db_entry.get("eprint")
    if db_entry.get("archiveprefix") in ("arxiv", "arXiv"):
        if eprint:
            identifiers.append(KeyId(RemoteKey.ARXIV, str(eprint)))

    return (str(db_entry["ID"]), identifiers)


def get_max_priority(keys: Iterable[KeyId]) -> KeyId:
    return sorted([ArchiveRecord(keyid).priority_key() for keyid in keys])[0]


def make_record_lookup(bibfile: Path) -> dict[str, str]:
    """Convert a bibfile into a dictionary mapping keys to possible identifiers."""
    bth = BibTexHandler()
    db = bth.loads(bibfile.read_text())
    candidates = dict(find_identifiers(entry) for entry in db.entries)
    return {k: str(get_max_priority(v)) for k, v in candidates.items() if len(v) > 0}


def get_citekeys(path: Path) -> Iterable[str]:
    CITEKEY_REGEX: Final = re.compile(
        r"(?<!\\)%.+|(\\(?:|paren|foot|text|super|auto|no)citep?\{((?!\*)[^{}]+)\})"
    )
    KEY_REGEX: Final = re.compile(r"([0-9a-zA-Z\.\-:_/]+)")

    cite_commands = (
        m.group(2) for m in CITEKEY_REGEX.finditer(path.read_text()) if m.group(2)
    )
    return set(chain.from_iterable(KEY_REGEX.findall(k) for k in cite_commands))


def cite_file_search(*paths: Path) -> Iterable[ArchiveRecord]:
    """Open the file at `path`, parse for citation commands, and
    generate the corresponding list of ArchiveRecord,"""

    SEARCHKEY_REGEX: Final = re.compile(r"((?:arxiv|doi|zbmath|zbl):(?:[\d\.]+))")

    # search for all citation commands
    cite_commands = chain.from_iterable(get_citekeys(path) for path in paths)

    # then parse each citation command to find a valid key
    cmds = set(chain.from_iterable(SEARCHKEY_REGEX.findall(k) for k in cite_commands))

    return (ArchiveRecord.from_keyid(keyid) for keyid in cmds)


def generate_biblatex(*paths: Path) -> str:
    """Generate the biblatex file associated with the citations inside a given file."""
    bth = BibTexHandler()
    return bth.write_records(cite_file_search(*paths))
