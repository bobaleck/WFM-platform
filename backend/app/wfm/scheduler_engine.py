from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(frozen=True)
class Candidate:
    employee_id: int
    skill_levels: dict[int, int]
    weekly_hours: float = 0
    assignments_count: int = 0
    last_shift_end: datetime | None = None
    absences: list[tuple[date, date]] | None = None


@dataclass(frozen=True)
class SchedulerSettings:
    max_weekly_hours: float = 40
    min_rest_hours: int = 12
    coverage_weight: int = 100
    skill_priority_weight: int = 50
    fairness_weight: int = 30


@dataclass(frozen=True)
class CandidateScore:
    employee_id: int
    total_score: float
    coverage_score: float
    skill_score: float
    fairness_score: float
    rest_score: float
    weekly_hours_score: float
    eligible: bool
    reason: str = ""


def has_absence(candidate: Candidate, work_date: date) -> bool:
    return any(start <= work_date <= end for start, end in (candidate.absences or []))


def matches_required_skills(skill_levels: dict[int, int], required_skills: list[tuple[int, int, bool]]) -> bool:
    for skill_id, min_level, is_required in required_skills:
        if is_required and skill_levels.get(skill_id, 0) < min_level:
            return False
    return True


def score_candidate(
    candidate: Candidate,
    required_skills: list[tuple[int, int, bool]],
    work_date: date,
    shift_start: datetime,
    shift_hours: float,
    settings: SchedulerSettings,
) -> CandidateScore:
    if has_absence(candidate, work_date):
        return CandidateScore(candidate.employee_id, -1, 0, 0, 0, 0, 0, False, "absence_conflict")
    if not matches_required_skills(candidate.skill_levels, required_skills):
        return CandidateScore(candidate.employee_id, -1, 0, 0, 0, 0, 0, False, "skill_gap")
    if candidate.weekly_hours + shift_hours > settings.max_weekly_hours:
        return CandidateScore(candidate.employee_id, -1, 0, 0, 0, 0, 0, False, "weekly_hours_limit")

    coverage_score = float(settings.coverage_weight)
    skill_score = sum(candidate.skill_levels.get(skill_id, 0) for skill_id, _min_level, _required in required_skills) * settings.skill_priority_weight / 5
    fairness_score = max(0.0, settings.fairness_weight - candidate.assignments_count * 5)
    if candidate.last_shift_end is None:
        rest_score = 20.0
    else:
        rest_hours = (shift_start - candidate.last_shift_end).total_seconds() / 3600
        rest_score = 20.0 if rest_hours >= settings.min_rest_hours else -50.0
    hours_ratio = (candidate.weekly_hours + shift_hours) / settings.max_weekly_hours if settings.max_weekly_hours else 1
    weekly_hours_score = max(-40.0, 30.0 * (1 - hours_ratio))
    total = coverage_score + skill_score + fairness_score + rest_score + weekly_hours_score
    return CandidateScore(candidate.employee_id, total, coverage_score, skill_score, fairness_score, rest_score, weekly_hours_score, True)


def choose_best_candidate(
    candidates: list[Candidate],
    required_skills: list[tuple[int, int, bool]],
    work_date: date,
    shift_start: datetime,
    shift_hours: float,
    settings: SchedulerSettings,
) -> CandidateScore | None:
    scores = [
        score_candidate(candidate, required_skills, work_date, shift_start, shift_hours, settings)
        for candidate in candidates
    ]
    eligible = [score for score in scores if score.eligible]
    if not eligible:
        return None
    return sorted(eligible, key=lambda score: (-score.total_score, score.employee_id))[0]


def previous_day(value: date) -> date:
    return value - timedelta(days=1)
