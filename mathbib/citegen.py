from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Final, Optional
    from .session import CLISession

from itertools import chain
from pathlib import Path
import re

from .record import ArchiveRecord
from .term import TermWrite
from .remote import KeyIdError


def get_citekeys(tex: str) -> frozenset[str]:
    """Retern an iterable of all citation keys contained in the provided string."""
    # a citation is a non-commented string of the form
    # \<citecommand>[...]{key1, key2, ...} first match for {key1, key2, ...}
    # and then extract the keys
    rx_citecommand = re.compile(
        r"(?<!\\)%.+|(\\(?:|paren|foot|text|super|auto|no|full)citep?"
        r"(?:\[[^\]]*\])?\{((?!\*)[^{}]+)\})"
    )
    rx_citekey: Final = re.compile(r"([^\s,{}\[\]\(\)\\%#~]+)")

    cite_commands = (
        match.group(2) for match in rx_citecommand.finditer(tex) if match.group(2)
    )

    return frozenset(chain.from_iterable(rx_citekey.findall(k) for k in cite_commands))


def get_citekeys_from_paths(*paths: Path) -> frozenset[str]:
    return frozenset(
        chain.from_iterable(get_citekeys(path.read_text()) for path in paths)
    )


def citekey_to_record(
    session: CLISession, citekey: str, alias: dict[str, str]
) -> Optional[ArchiveRecord]:
    """Convert a citation key to an ArchiveRecord if possible.

    Warning: the returned ArchiveRecord might be a null record.
    """
    aliased = alias.get(citekey)
    try:
        if aliased is not None:
            return ArchiveRecord.from_str(aliased, alias=citekey, session=session)
        else:
            return ArchiveRecord.from_str(citekey, session=session)

    except KeyIdError:
        TermWrite.warn(f"Could not find KEY:ID associated with '{citekey}'.")
        return None


def multiple_replace(dct: dict[str, str], text: str):
    # Create a regular expression  from the dctionary keys
    regex = re.compile("(%s)" % "|".join(map(re.escape, dct.keys())))

    # For each match, look-up corresponding value in dctionary
    return regex.sub(lambda mo: dct[mo.string[mo.start() : mo.end()]], text)


def get_file_records(session: CLISession, *paths: Path) -> Iterable[ArchiveRecord]:
    """Open the file at `path`, parse for citation commands, and
    generate the corresponding list of ArchiveRecord."""

    citekeys = get_citekeys_from_paths(*paths)

    records_or_none = (
        citekey_to_record(session, citekey, session.alias) for citekey in citekeys
    )

    return (record for record in records_or_none if record is not None)


def generate_biblatex(session: CLISession, *paths: Path) -> str:
    """Generate the biblatex file associated with the citations inside a given file."""
    return session.bibtex_handler.write_records(get_file_records(session, *paths))
