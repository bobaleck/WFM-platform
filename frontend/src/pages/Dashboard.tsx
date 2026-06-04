import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { endpoints, getSummary, type AnyRecord, type Summary } from "../api/wfm";
import { Alert } from "../components/Alert";
import { DataTable } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";
import { SectionCard } from "../components/SectionCard";

type ExecutiveSummary = {
  active_employees: number;
  published_assignments: number;
  avg_coverage_percent: number;
  gap_intervals_count: number;
  avg_service_level_percent: number;
  avg_aht_sec: number;
  planned_hours: number;
  actual_hours: number;
  adherence_percent: number;
};

export function Dashboard() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [executive, setExecutive] = useState<ExecutiveSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      getSummary(),
      apiGet<ExecutiveSummary>(endpoints.executiveSummary)
    ]).then(([summaryData, executiveData]) => {
      setSummary(summaryData);
      setExecutive(executiveData);
    }).catch(() => setError("Не удалось загрузить управленческую сводку"));
  }, []);

  if (error) {
    return <SectionCard><Alert type="error">{error}</Alert></SectionCard>;
  }

  if (!summary || !executive) {
    return <SectionCard>Загрузка управленческой сводки...</SectionCard>;
  }

  const lastGeneration = summary.recent_generations[0] as AnyRecord | undefined;

  return (
    <>
      <section className="kpi-grid">
        <KpiCard label="Активные сотрудники" value={executive.active_employees} />
        <KpiCard label="Опубликованные графики" value={executive.published_assignments} />
        <KpiCard label="Среднее покрытие" value={`${executive.avg_coverage_percent}%`} />
        <KpiCard label="Интервалы с дефицитом" value={executive.gap_intervals_count} />
        <KpiCard label="SLA" value={`${executive.avg_service_level_percent}%`} />
        <KpiCard label="AHT" value={`${executive.avg_aht_sec} сек`} />
        <KpiCard label="Плановые часы" value={executive.planned_hours} />
        <KpiCard label="Фактические часы" value={executive.actual_hours} />
        <KpiCard label="Adherence" value={`${executive.adherence_percent}%`} />
        <KpiCard label="Последний запуск генерации" value={lastGeneration ? String(lastGeneration.date_from) : "нет"} />
      </section>

      <section className="dashboard-grid">
        <SectionCard title="Операционная сводка" description="Очереди, нагрузка и потребность по контакт-центру.">
          <DataTable columns={[
            { key: "queue_name", label: "Очередь" },
            { key: "required_agents", label: "Требуется" },
            { key: "planned_agents", label: "План" },
            { key: "gap_agents", label: "Дефицит" }
          ]} rows={summary.staffing_by_queue} />
        </SectionCard>

        <SectionCard title="Дефициты покрытия" description="Интервалы, где план не закрывает потребность.">
          <DataTable columns={[
            { key: "interval_start", label: "Интервал", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
            { key: "queue_name", label: "Очередь" },
            { key: "gap_agents", label: "Дефицит" },
            { key: "coverage_percent", label: "Покрытие" }
          ]} rows={summary.coverage_gaps} />
        </SectionCard>

        <SectionCard title="Графики на сегодня" description="Короткий список назначений на текущую дату сервера.">
          <DataTable columns={[
            { key: "employee_name", label: "Сотрудник" },
            { key: "shift_name", label: "Смена" },
            { key: "queue_name", label: "Очередь" },
            { key: "status", label: "Статус" }
          ]} rows={summary.today_schedules} />
        </SectionCard>

        <SectionCard title="План/факт за неделю" description="Сравнение плановых и фактических часов.">
          <div className="kpi-grid compact">
            <KpiCard label="План" value={String(summary.plan_fact.planned_hours ?? 0)} />
            <KpiCard label="Факт" value={String(summary.plan_fact.actual_hours ?? 0)} />
            <KpiCard label="Adherence" value={`${String(summary.plan_fact.adherence_percent ?? 0)}%`} />
          </div>
        </SectionCard>

        <SectionCard title="Последние действия" description="Импорты и генерации, влияющие на WFM-контур.">
          <DataTable columns={[
            { key: "filename", label: "Файл" },
            { key: "status", label: "Статус" },
            { key: "rows_success", label: "Успешно" },
            { key: "rows_failed", label: "Ошибки" }
          ]} rows={summary.recent_imports} />
        </SectionCard>
      </section>
    </>
  );
}
