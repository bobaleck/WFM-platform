import { apiGet, apiPost, apiPostForm, apiPut, getToken } from "./client";

export type AnyRecord = Record<string, unknown>;

export type Summary = {
  total_employees: number;
  active_teams: number;
  queues: number;
  shifts: number;
  week_assignments: number;
  average_service_level: number;
  average_aht: number;
  staffing_gap: number;
  kpi: Record<string, number>;
  staffing_by_queue: AnyRecord[];
  planned_coverage: AnyRecord[];
  recent_imports: AnyRecord[];
  today_schedules: AnyRecord[];
  coverage_gaps: AnyRecord[];
  recent_generations: AnyRecord[];
  plan_fact: AnyRecord;
};

export type Project = {
  id: number;
  project_uuid: string;
  title: string;
  is_active: boolean;
  is_default: boolean;
};

export type Contour = {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  is_default: boolean;
};

export type WorkContext = {
  context_type: "project" | "partner";
  id: number;
  title: string;
  uuid: string;
};

export const endpoints = {
  employees: "/api/v1/employees",
  teams: "/api/v1/teams",
  skills: "/api/v1/skills",
  queues: "/api/v1/queues",
  workload: "/api/v1/workload",
  staffing: "/api/v1/staffing",
  shifts: "/api/v1/shifts",
  schedules: "/api/v1/schedules",
  coverage: "/api/v1/coverage",
  absences: "/api/v1/absences",
  imports: "/api/v1/imports",
  planningSettings: "/api/v1/planning/settings",
  calculateStaffing: "/api/v1/planning/calculate-staffing",
  scheduleRules: "/api/v1/schedule-rules",
  generateDraft: "/api/v1/schedules/generate-draft",
  confirmPeriod: "/api/v1/schedules/confirm-period",
  publishPeriod: "/api/v1/schedules/publish-period",
  recalculateCoverage: "/api/v1/schedules/recalculate-coverage",
  recommendations: "/api/v1/schedule-recommendations",
  planFact: "/api/v1/reports/plan-fact",
  summary: "/api/v1/reports/summary",
  executiveSummary: "/api/v1/reports/executive-summary",
  operationsSummary: "/api/v1/reports/operations-summary",
  staffingEfficiency: "/api/v1/reports/staffing-efficiency",
  coverageGaps: "/api/v1/reports/coverage-gaps",
  slaSummary: "/api/v1/reports/sla-summary"
};

export function getList(path: string): Promise<AnyRecord[]> {
  return apiGet<AnyRecord[]>(path);
}

export function getSummary(): Promise<Summary> {
  return apiGet<Summary>(endpoints.summary);
}

export function uploadWorkloadCsv(file: File): Promise<AnyRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<AnyRecord>("/api/v1/imports/workload-csv", formData);
}

export function uploadWorkloadCsvNew(file: File): Promise<AnyRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<AnyRecord>("/api/v1/workload/import/csv", formData);
}

export function uploadWorkloadXlsx(file: File): Promise<AnyRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<AnyRecord>("/api/v1/workload/import/xlsx", formData);
}

export async function downloadWorkloadTemplate(): Promise<void> {
  const response = await fetch("/api/v1/workload/template.xlsx", { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!response.ok) throw new Error(`Шаблон нагрузки не получен: ${response.status}`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "workload-template.xlsx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function uploadEmployeeRegistry(file: File): Promise<AnyRecord> {
  const formData = new FormData();
  formData.append("file", file);
  return apiPostForm<AnyRecord>("/api/v1/employees/import/xlsx", formData);
}

export function checkEmployeeOneC(id: number): Promise<AnyRecord> {
  return apiPost<AnyRecord>(`/api/v1/employees/${id}/check-1c-status`, {});
}

export function checkAllEmployeesOneC(only_active = true): Promise<AnyRecord> {
  return apiPost<AnyRecord>("/api/v1/employees/check-all-1c-status", { only_active });
}

export function checkEmployeeNaumen(id: number): Promise<AnyRecord> {
  return apiPost<AnyRecord>(`/api/v1/employees/${id}/check-naumen`, {});
}

export function checkEmployeeNaumenUuid(id: number): Promise<AnyRecord> {
  return apiPost<AnyRecord>(`/api/v1/employees/${id}/check-naumen-uuid`, {});
}

export function updateEmployeeNaumenLink(id: number, payload: AnyRecord): Promise<AnyRecord> {
  return apiPut<AnyRecord>(`/api/v1/employees/${id}/naumen-link`, payload);
}

export function updateEmployeeSkills(id: number, skill_ids: number[]): Promise<AnyRecord> {
  return apiPut<AnyRecord>(`/api/v1/employees/${id}/skills`, { skill_ids });
}

export function matchNaumenOperators(): Promise<AnyRecord> {
  return apiPost<AnyRecord>("/api/v1/employees/naumen/match", {});
}

export function checkAllEmployeesNaumen(): Promise<AnyRecord> {
  return apiPost<AnyRecord>("/api/v1/employees/naumen/check-all", {});
}

export function syncNaumenOperators(): Promise<AnyRecord> {
  return apiPost<AnyRecord>("/api/v1/naumen/operators/sync", {});
}

export async function downloadEmployeeTemplate(): Promise<void> {
  const response = await fetch("/api/v1/employees/import/template.xlsx", { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!response.ok) {
    throw new Error(`Шаблон не получен: ${response.status}`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "employee-registry-template.xlsx";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function calculateStaffing(date_from: string, date_to: string): Promise<AnyRecord> {
  return apiPost<AnyRecord>(endpoints.calculateStaffing, { date_from, date_to });
}

export function generateDraftSchedule(date_from: string, date_to: string): Promise<AnyRecord> {
  return apiPost<AnyRecord>(endpoints.generateDraft, { date_from, date_to, queue_id: null });
}

export function confirmPeriod(date_from: string, date_to: string): Promise<AnyRecord> {
  return apiPost<AnyRecord>(endpoints.confirmPeriod, { date_from, date_to, queue_id: null });
}

export function publishPeriod(date_from: string, date_to: string): Promise<AnyRecord> {
  return apiPost<AnyRecord>(endpoints.publishPeriod, { date_from, date_to, queue_id: null });
}

export function recalculateCoverage(date_from: string, date_to: string): Promise<AnyRecord> {
  return apiPost<AnyRecord>(endpoints.recalculateCoverage, { date_from, date_to, queue_id: null });
}

export function updateScheduleStatus(id: number, action: "confirm" | "publish" | "cancel"): Promise<AnyRecord> {
  return apiPost<AnyRecord>(`/api/v1/schedules/${id}/${action}`, {});
}

export function getProjects(): Promise<Project[]> {
  return apiGet<Project[]>("/api/v1/projects");
}

export function getCurrentProject(): Promise<Project | null> {
  return apiGet<Project | null>("/api/v1/projects/current");
}

export function setCurrentProject(project_id: number | null): Promise<Project | null> {
  return apiPut<Project | null>("/api/v1/projects/current", { project_id });
}

export function getCurrentContext(): Promise<WorkContext | null> {
  return apiGet<WorkContext | null>("/api/v1/projects/current-context");
}

export function setCurrentContext(context_type: "project" | "partner" | null, id: number | null): Promise<WorkContext | null> {
  return apiPut<WorkContext | null>("/api/v1/projects/current-context", { context_type, id });
}

export function getContours(): Promise<Contour[]> {
  return apiGet<Contour[]>("/api/v1/contours");
}

export function getCurrentContour(): Promise<Contour | null> {
  return apiGet<Contour | null>("/api/v1/contours/current");
}

export function setCurrentContour(id: number | null): Promise<Contour | null> {
  return apiPut<Contour | null>("/api/v1/contours/current", { id });
}

export async function downloadCsv(path: string, filename: string): Promise<void> {
  const response = await fetch(path, { headers: { Authorization: `Bearer ${getToken()}` } });
  if (response.status === 401) {
    throw new Error("Требуется авторизация");
  }
  if (response.status === 403) {
    throw new Error("Нет доступа к выгрузке");
  }
  if (!response.ok) {
    throw new Error(`Выгрузка не выполнена: ${response.status}`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
