from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from .remote import RelatedRecords, URLBuilder, RemoteRecord, KeyId

from datetime import datetime
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from . import __version__
from .term import TermWrite
from .remote import REMOTES
from .remote.error import RemoteAccessError, RemoteParseError


class NullRecordError(Exception):
    def __init__(self, keyid: KeyId):
        self.keyid = keyid
        super().__init__("KEY:ID '{keyid}' is a null record.")


def make_request(identifier: str, build_url: URLBuilder) -> Optional[str]:
    url = build_url(identifier)

    TermWrite.remote(url)

    req = Request(url)
    req.add_header(
        "User-Agent", f"MathBib/{__version__} (mailto:api-contact@rutar.org)"
    )

    try:
        with urlopen(req) as fp:
            return fp.read().decode("utf8")

    except (HTTPError, RemoteAccessError, RemoteParseError):
        return


def serialize(keyid: KeyId, record: Optional[dict], related: Optional[dict[str, str]]
) -> None:
    target = keyid.cache_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    cache_object = {
        "record": record,
        "accessed": datetime.now().isoformat(),
        "related": related,
    }
    target.write_text(json.dumps(cache_object))

def _load_cached_record(keyid: KeyId) -> tuple[Optional[dict], dict[str, str]]:
    cache = json.loads(keyid.cache_path().read_text())
    return cache["record"], cache["related"]

def delete_cached_record(keyid: KeyId):
    cache_file = keyid.cache_path()
    cache_file.unlink(missing_ok=True)

def resolve_related(
    keyid: KeyId, related: RelatedRecords
) -> dict[str, str]:
    related_identifiers = {str(keyid.key): keyid.identifier}

    for key, res in related.items():
        if isinstance(res, str):
            related_identifiers[key] = res
        else:
            url_builder, parser = res
            response = make_request(keyid.identifier, url_builder)
            if response is not None:
                parsed = parser(response)
                if parsed is not None:
                    related_identifiers[key] = parsed

    return related_identifiers

def _load_remote_record(remote_record: RemoteRecord, keyid: KeyId) -> tuple[Optional[dict], dict[str, str]]:
    """Load and parse the remote record."""
    response = make_request(keyid.identifier, remote_record.build_url)
    if response is not None:
        record, related = remote_record.parse_record(response)
        return (record, resolve_related(keyid, related))
    else:
        return None, {}

def load_record(keyid: KeyId) -> tuple[Optional[dict], dict[str, str]]:
    """Load the item identifier, defaulting to the cache if possible and
    writing to the cache after loading.

    If the identifier is invalid, return a null record.
    """
    remote_record = REMOTES[keyid.key]

    if not remote_record.validate_identifier(keyid.identifier):
        return None, {}

    try:
        cache = _load_cached_record(keyid)
    except FileNotFoundError:
        cache = None

    if cache is None:
        record, related = _load_remote_record(remote_record, keyid)
        serialize(keyid, record, related)
        return record, related

    else:
        record, related = cache

    return (record, related)
