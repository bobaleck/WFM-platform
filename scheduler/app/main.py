from math import ceil

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="wfm-naumen-scheduler", version="0.1.0")


class CalculatePreviewIn(BaseModel):
    offered_contacts: int = Field(ge=0)
    average_handle_time_sec: int = Field(ge=0)
    interval_minutes: int = Field(default=30, ge=1)
    target_occupancy: float = Field(default=0.85, gt=0, le=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "scheduler"}


@app.get("/api/v1/scheduler/status")
def scheduler_status() -> dict[str, str]:
    return {
        "status": "idle",
        "optimizer": "planned",
        "service": "scheduler",
    }


@app.post("/api/v1/scheduler/draft-schedule")
def draft_schedule() -> dict[str, str]:
    return {
        "status": "not_implemented",
        "message": "Расчёт графиков будет реализован на следующем этапе.",
    }


@app.post("/api/v1/scheduler/calculate-preview")
def calculate_preview(payload: CalculatePreviewIn) -> dict[str, int | str]:
    if payload.offered_contacts == 0:
        required_agents = 0
    else:
        workload_seconds = payload.offered_contacts * payload.average_handle_time_sec
        interval_seconds = payload.interval_minutes * 60
        required_agents = max(1, ceil((workload_seconds / interval_seconds) / payload.target_occupancy))
    return {
        "required_agents": required_agents,
        "explanation": "Расчёт выполнен по MVP-формуле",
    }
