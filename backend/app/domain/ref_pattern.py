from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)
PROJECT_ID_RE = re.compile(r'^[A-Za-z0-9_]+$')
# Short identifier PROJECT_ID-TYPE-N. project_id excludes '-', type tokens are
# fixed, so the '-' splits are unambiguous.
_ENTITY_TYPES = "UI_AREA|FEATURE|INFRA_UNIT|API|CODE_SYMBOL|ISSUE"
SHORT_ID_RE = re.compile(
    rf'^(?P<pid>[A-Za-z0-9_]+)-(?P<type>{_ENTITY_TYPES})-(?P<n>\d+)$'
)


class RefKind(str, Enum):
    UUID = "uuid"
    SCOPED_UUID = "scoped_uuid"
    SCOPED_TAG = "scoped_tag"
    SHORT_ID = "short_id"


@dataclass
class ParsedRef:
    kind: RefKind
    project_id: str | None
    identifier: str
    entity_type: str | None = None
    short_seq: int | None = None


def parse_ref(ref: str) -> ParsedRef:
    """Parse a reference string into a structured form.

    Raises ValueError for malformed input.
    """
    if not ref or not ref.strip():
        raise ValueError("Reference must not be empty")

    if '@' not in ref:
        if UUID_RE.match(ref):
            return ParsedRef(kind=RefKind.UUID, project_id=None, identifier=ref.lower())
        m = SHORT_ID_RE.match(ref)
        if m:
            return ParsedRef(
                kind=RefKind.SHORT_ID,
                project_id=m.group("pid"),
                identifier=ref,
                entity_type=m.group("type"),
                short_seq=int(m.group("n")),
            )
        raise ValueError(
            f"Invalid reference: {ref!r} — expected UUID, PROJECT_ID-TYPE-N, or PROJECT_ID@identifier"
        )

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
