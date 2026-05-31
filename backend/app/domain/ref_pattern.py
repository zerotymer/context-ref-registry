from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)
PROJECT_ID_RE = re.compile(r'^[A-Za-z0-9_]+$')


class RefKind(str, Enum):
    UUID = "uuid"
    SCOPED_UUID = "scoped_uuid"
    SCOPED_TAG = "scoped_tag"


@dataclass
class ParsedRef:
    kind: RefKind
    project_id: str | None
    identifier: str


def parse_ref(ref: str) -> ParsedRef:
    """Parse a reference string into a structured form.

    Raises ValueError for malformed input.
    """
    if not ref or not ref.strip():
        raise ValueError("Reference must not be empty")

    if '@' not in ref:
        if not UUID_RE.match(ref):
            raise ValueError(f"Invalid reference: {ref!r} — expected UUID or PROJECT_ID@identifier")
        return ParsedRef(kind=RefKind.UUID, project_id=None, identifier=ref.lower())

    parts = ref.split('@', 1)
    project_id, rest = parts[0], parts[1]

    if not PROJECT_ID_RE.match(project_id):
        raise ValueError(f"Invalid project_id in reference: {project_id!r}")
    if not rest:
        raise ValueError(f"Identifier after '@' must not be empty in: {ref!r}")

    if UUID_RE.match(rest):
        return ParsedRef(kind=RefKind.SCOPED_UUID, project_id=project_id, identifier=rest.lower())
    else:
        return ParsedRef(kind=RefKind.SCOPED_TAG, project_id=project_id, identifier=rest)
