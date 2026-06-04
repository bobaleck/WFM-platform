from __future__ import annotations

import math
from datetime import datetime


def calculate_required_agents(
    offered_contacts: int,
    average_handle_time_sec: int,
    interval_start: datetime | None = None,
    interval_end: datetime | None = None,
    interval_minutes: int | None = None,
    target_occupancy: float = 0.85,
    min_agents_per_queue: int = 1,
    shrinkage_percent: float = 0,
) -> int:
    if offered_contacts <= 0:
        return 0

    if interval_start and interval_end:
        interval_seconds = max(1, int((interval_end - interval_start).total_seconds()))
    else:
        interval_seconds = max(1, int((interval_minutes or 30) * 60))

    occupancy = target_occupancy if target_occupancy > 0 else 0.85
    workload_seconds = offered_contacts * max(0, average_handle_time_sec)
    raw_agents = workload_seconds / interval_seconds
    base_required = math.ceil(raw_agents / occupancy)
    shrinkage = min(max(shrinkage_percent, 0), 95)
    required_agents = math.ceil(base_required / (1 - shrinkage / 100)) if shrinkage else base_required
    return max(min_agents_per_queue, required_agents)


def calculation_note(
    offered_contacts: int,
    average_handle_time_sec: int,
    target_occupancy: float,
    shrinkage_percent: float,
    method: str,
) -> str:
    return (
        f"method={method}; offered_contacts={offered_contacts}; "
        f"AHT={average_handle_time_sec}; target_occupancy={target_occupancy}; "
        f"shrinkage_percent={shrinkage_percent}"
    )


def employee_matches_required_skills(
    employee_skills: dict[int, int],
    required_skills: list[tuple[int, int, bool]],
) -> bool:
    for skill_id, min_level, is_required in required_skills:
        if is_required and employee_skills.get(skill_id, 0) < min_level:
            return False
    return True


def skill_match_score(
    employee_skills: dict[int, int],
    required_skills: list[tuple[int, int, bool]],
) -> int:
    score = 0
    for skill_id, min_level, _is_required in required_skills:
        level = employee_skills.get(skill_id, 0)
        if level >= min_level:
            score += level
    return score


def coverage_percent(planned_agents: int, required_agents: int) -> float:
    if required_agents <= 0:
        return 0
    return round(planned_agents / required_agents * 100, 1)
