from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NaumenEmployee:
    external_id: str
    login: str
    full_name: str
    email: str | None = None
    department: str | None = None
    removed: bool = False
