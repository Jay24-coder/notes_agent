from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from itw.errors import ItwError


@dataclass(frozen=True)
class RawNote:
    note_id: str
    source_path: str
    title: str
    content: str


def stable_note_id(source_path: str) -> str:
    normalized = str(Path(source_path).resolve())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def read_note_file(path: Path) -> RawNote:
    if not path.is_file():
        raise ItwError(f"Note file not found: {path}")
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ItwError(f"Could not read note file {path}: {exc}") from exc

    if not content:
        raise ItwError(f"Note file is empty: {path}")

    source = str(path.resolve())
    return RawNote(
        note_id=stable_note_id(source),
        source_path=source,
        title=path.stem,
        content=content,
    )


def new_created_at() -> int:
    return int(time.time())
