import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { downloadCsv, endpoints, type AnyRecord } from "../api/wfm";
import { Alert } from "../components/Alert";
import { DataTable } from "../components/DataTable";
import { DateRangeFilter } from "../components/DateRangeFilter";
import { KpiCard } from "../components/KpiCard";
import { SectionCard } from "../components/SectionCard";

type TabKey = "executive" | "operations" | "coverage" | "planfact" | "sla" | "exports";

const tabs: Array<{ key: TabKey; label: string }> = [
  { key: "executive", label: "Руководитель" },
  { key: "operations", label: "Операции" },
  { key: "coverage", label: "Покрытие" },
  { key: "planfact", label: "План/факт" },
  { key: "sla", label: "SLA" },
  { key: "exports", label: "Экспорты" }
];

export function Reports() {
  const [activeTab, setActiveTab] = useState<TabKey>("executive");
  const [executive, setExecutive] = useState<AnyRecord | null>(null);
  const [operations, setOperations] = useState<AnyRecord[]>([]);
  const [efficiency, setEfficiency] = useState<AnyRecord | null>(null);
  const [coverageGaps, setCoverageGaps] = useState<AnyRecord[]>([]);
  const [sla, setSla] = useState<AnyRecord[]>([]);
  const [planFact, setPlanFact] = useState<AnyRecord | null>(null);
  const [exportsLog, setExportsLog] = useState<AnyRecord[]>([]);
  const [dateFrom, setDateFrom] = useState("2026-01-15");
  const [dateTo, setDateTo] = useState("2026-01-21");
  const [error, setError] = useState("");
  const [exportMessage, setExportMessage] = useState("");
  const [exporting, setExporting] = useState("");

  const loadPlanFact = () => apiGet<AnyRecord>(`${endpoints.planFact}?date_from=${dateFrom}&date_to=${dateTo}`).then(setPlanFact);

  const loadReports = () => {
    setError("");
    Promise.all([
      apiGet<AnyRecord>(endpoints.executiveSummary),
      apiGet<AnyRecord[]>(endpoints.operationsSummary),
      apiGet<AnyRecord>(endpoints.staffingEfficiency),
      apiGet<AnyRecord[]>(endpoints.coverageGaps),
      apiGet<AnyRecord[]>(endpoints.slaSummary),
      loadPlanFact(),
      apiGet<AnyRecord[]>("/api/v1/reports/export-log")
    ]).then(([executiveData, operationsData, efficiencyData, coverageData, slaData, _planFactData, exportsData]) => {
      setExecutive(executiveData);
      setOperations(operationsData);
      setEfficiency(efficiencyData);
      setCoverageGaps(coverageData);
      setSla(slaData);
      setExportsLog(exportsData);
    }).catch(() => setError("Не удалось загрузить отчёты"));
  };

  useEffect(() => {
    loadReports();
  }, []);

  useEffect(() => {
    loadPlanFact().catch(() => setPlanFact(null));
  }, [dateFrom, dateTo]);

  const planFactRows = Array.isArray(planFact?.rows) ? planFact.rows as AnyRecord[] : [];
  const today = new Date().toISOString().slice(0, 10);
  const exportFile = async (path: string, filename: string) => {
    setError("");
    setExportMessage("");
    setExporting(path);
    try {
      await downloadCsv(path, filename);
      setExportMessage("Файл выгружен");
      loadReports();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Выгрузка не выполнена");
    } finally {
      setExporting("");
    }
  };

  return (
    <>
      <div className="tabs">
        {tabs.map((tab) => (
          <button key={tab.key} type="button" className={activeTab === tab.key ? "is-active" : ""} onClick={() => setActiveTab(tab.key)}>
            {tab.label}
          </button>
        ))}
      </div>
      {error ? <SectionCard><Alert type="error">{error}</Alert></SectionCard> : null}
      {exportMessage ? <SectionCard><Alert>{exportMessage}</Alert></SectionCard> : null}

      {activeTab === "executive" && executive ? (
        <SectionCard title="Руководитель" description="Ключевые показатели WFM-платформы для управленческого контроля." actions={<button type="button" onClick={() => exportFile("/api/v1/reports/executive-summary.csv", `executive-summary_${today}.csv`)} disabled={Boolean(exporting)}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
          <div className="kpi-grid compact">
            <KpiCard label="Активные сотрудники" value={String(executive.active_employees ?? 0)} />
            <KpiCard label="Активные очереди" value={String(executive.active_queues ?? 0)} />
            <KpiCard label="Опубликованные графики" value={String(executive.published_assignments ?? 0)} />
            <KpiCard label="Среднее покрытие" value={`${String(executive.avg_coverage_percent ?? 0)}%`} />
            <KpiCard label="Дефицитные интервалы" value={String(executive.gap_intervals_count ?? 0)} />
            <KpiCard label="SLA" value={`${String(executive.avg_service_level_percent ?? 0)}%`} />
            <KpiCard label="AHT" value={`${String(executive.avg_aht_sec ?? 0)} сек`} />
            <KpiCard label="Adherence" value={`${String(executive.adherence_percent ?? 0)}%`} />
          </div>
        </SectionCard>
      ) : null}

      {activeTab === "operations" ? (
        <SectionCard title="Операции" description="Нагрузка, обработка и потребность по дням и очередям." actions={<button type="button" onClick={() => exportFile("/api/v1/reports/operations-summary.csv", `operations-summary_${today}.csv`)} disabled={Boolean(exporting)}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
          <DataTable columns={[
            { key: "work_date", label: "Дата" },
            { key: "queue_name", label: "Очередь" },
            { key: "offered_contacts", label: "Поступило" },
            { key: "handled_contacts", label: "Обработано" },
            { key: "abandoned_contacts", label: "Потеряно" },
            { key: "avg_aht_sec", label: "AHT" },
            { key: "avg_service_level_percent", label: "SL" },
            { key: "required_agents", label: "Требуется" },
            { key: "planned_agents", label: "План" },
            { key: "gap_agents", label: "Дефицит" }
          ]} rows={operations} />
        </SectionCard>
      ) : null}

      {activeTab === "coverage" ? (
        <SectionCard title="Покрытие" description="Интервалы с нехваткой плановых назначений." actions={<button type="button" onClick={() => exportFile("/api/v1/reports/coverage-gaps.csv", `coverage_${today}.csv`)} disabled={Boolean(exporting)}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
          <DataTable columns={[
            { key: "interval_start", label: "Начало", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
            { key: "queue_name", label: "Очередь" },
            { key: "required_agents", label: "Требуется" },
            { key: "planned_agents", label: "План" },
            { key: "gap_agents", label: "Дефицит" },
            { key: "severity", label: "Важность", render: (row) => {
              const labels: Record<string, string> = { low: "Низкая", medium: "Средняя", high: "Высокая", critical: "Критичная" };
              return labels[String(row.severity)] || "Средняя";
            } }
          ]} rows={coverageGaps} />
        </SectionCard>
      ) : null}

      {activeTab === "planfact" ? (
        <SectionCard title="План/факт" description="Сравнение опубликованного плана и фактической работы." actions={<button type="button" onClick={() => exportFile(`/api/v1/reports/plan-fact.csv?date_from=${dateFrom}&date_to=${dateTo}`, `plan-fact_${today}.csv`)} disabled={Boolean(exporting)}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
          <div className="form-row">
            <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFrom={setDateFrom} onDateTo={setDateTo} />
            <button type="button" onClick={() => loadPlanFact().catch(() => setError("Не удалось обновить план/факт"))}>Обновить</button>
          </div>
          <div className="kpi-grid compact">
            <KpiCard label="Плановые часы" value={String(planFact?.planned_hours ?? 0)} />
            <KpiCard label="Фактические часы" value={String(planFact?.actual_hours ?? 0)} />
            <KpiCard label="Расхождение" value={String(planFact?.gap_hours ?? 0)} />
            <KpiCard label="Adherence" value={`${String(planFact?.adherence_percent ?? 0)}%`} />
          </div>
          <DataTable columns={[
            { key: "work_date", label: "Дата" },
            { key: "employee_name", label: "Сотрудник" },
            { key: "queue_name", label: "Очередь" },
            { key: "status", label: "Факт" },
            { key: "actual_minutes", label: "Минуты" },
            { key: "actual_hours", label: "Часы" }
          ]} rows={planFactRows} />
        </SectionCard>
      ) : null}

      {activeTab === "sla" ? (
        <SectionCard title="SLA" description="Средний и минимальный service level по очередям." actions={<button type="button" onClick={() => exportFile("/api/v1/reports/sla-summary.csv", `sla-summary_${today}.csv`)} disabled={Boolean(exporting)}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
          <DataTable columns={[
            { key: "queue_name", label: "Очередь" },
            { key: "target_service_level_percent", label: "Цель" },
            { key: "avg_service_level_percent", label: "Средний SL" },
            { key: "min_service_level_percent", label: "Мин. SL" },
            { key: "below_target_intervals", label: "Ниже цели" },
            { key: "intervals_total", label: "Всего интервалов" }
          ]} rows={sla} />
        </SectionCard>
      ) : null}

      {activeTab === "exports" ? (
        <SectionCard title="Экспорты" description="Журнал CSV-выгрузок и дополнительные отчёты." actions={<button type="button" onClick={() => exportFile("/api/v1/reports/staffing-efficiency.csv", `staffing-efficiency_${today}.csv`)} disabled={Boolean(exporting)}>Выгрузить эффективность</button>}>
          <div className="kpi-grid compact">
            <KpiCard label="Плановые часы" value={String(efficiency?.planned_hours ?? 0)} />
            <KpiCard label="Фактические часы" value={String(efficiency?.actual_hours ?? 0)} />
            <KpiCard label="Utilization" value={`${String(efficiency?.utilization_percent ?? 0)}%`} />
            <KpiCard label="Дефицит часов" value={String(efficiency?.deficit_hours ?? 0)} />
          </div>
          <DataTable columns={[
            { key: "report_type", label: "Отчёт" },
            { key: "filename", label: "Файл" },
            { key: "rows_count", label: "Строк" },
            { key: "created_at", label: "Создано", render: (row) => String(row.created_at).replace("T", " ").slice(0, 16) }
          ]} rows={exportsLog} />
        </SectionCard>
      ) : null}
    </>
  );
}
