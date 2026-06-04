from __future__ import annotations

from app.integrations.naumen.schemas import NaumenEmployee


def parse_employee(payload: dict) -> NaumenEmployee:
    login = str(payload.get("login") or payload.get("uuid") or "")
    full_name = str(payload.get("title") or " ".join(filter(None, [payload.get("lastName"), payload.get("firstName"), payload.get("middleName")])) or login)
    return NaumenEmployee(
        external_id=str(payload.get("uuid") or login),
        login=login,
        full_name=full_name,
        email=payload.get("email"),
        department=payload.get("department") or payload.get("ou"),
        removed=bool(payload.get("removed")),
    )
