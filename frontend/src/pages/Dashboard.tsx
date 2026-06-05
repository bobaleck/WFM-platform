import { useEffect, useState } from "react";
import { apiGet } from "../api/client";
import { endpoints, getLocalNccStatus, getSummary, syncContourNaumen, getCurrentContour, type AnyRecord, type Summary } from "../api/wfm";
import { Alert } from "../components/Alert";
import { AsyncButton } from "../components/AsyncButton";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
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
  const [nccLocal, setNccLocal] = useState<AnyRecord | null>(null);
  const [error, setError] = useState("");
  const [syncing, setSyncing] = useState(false);

  const load = async () => {
    setError("");
    const [summaryResult, executiveResult, nccResult] = await Promise.allSettled([
      getSummary(),
      apiGet<ExecutiveSummary>(endpoints.executiveSummary),
      getLocalNccStatus()
    ]);
    if (summaryResult.status === "fulfilled") setSummary(summaryResult.value);
    if (executiveResult.status === "fulfilled") setExecutive(executiveResult.value);
    if (nccResult.status === "fulfilled") setNccLocal(nccResult.value);
    if (summaryResult.status === "rejected") setError("Не удалось загрузить базовую сводку WFM. Проверьте backend API.");
  };

  useEffect(() => { load(); }, []);

  const syncFromNaumen = async () => {
    setSyncing(true);
    setError("");
    try {
      const current = await getCurrentContour();
      if (!current) throw new Error("Контур не выбран");
      const end = new Date();
      end.setDate(end.getDate() + 1);
      const begin = new Date(end);
      begin.setDate(begin.getDate() - 7);
      await syncContourNaumen(current.id, begin.toISOString().slice(0, 10), end.toISOString().slice(0, 10));
      await load();
    } catch {
      setError("Загрузка из Naumen/NCC не выполнена. Проверьте UUID активного контура и NCC env на backend.");
    } finally {
      setSyncing(false);
    }
  };

  if (error) {
    return <SectionCard><Alert type="error">{error}</Alert></SectionCard>;
  }

  if (!summary) {
    return <SectionCard>Загрузка управленческой сводки...</SectionCard>;
  }

  const lastGeneration = summary.recent_generations[0] as AnyRecord | undefined;
  const safeExecutive = executive || {
    active_employees: summary.total_employees,
    published_assignments: summary.week_assignments,
    avg_coverage_percent: 0,
    gap_intervals_count: summary.coverage_gaps.length,
    avg_service_level_percent: summary.average_service_level,
    avg_aht_sec: summary.average_aht,
    planned_hours: Number(summary.plan_fact.planned_hours ?? 0),
    actual_hours: Number(summary.plan_fact.actual_hours ?? 0),
    adherence_percent: Number(summary.plan_fact.adherence_percent ?? 0)
  };
  const nccCounts = (nccLocal?.counts || {}) as Record<string, unknown>;
  const hasNccData = Object.values(nccCounts).some((value) => Number(value || 0) > 0);

  return (
    <>
      <section className="kpi-grid">
        <KpiCard label="Активные сотрудники" value={safeExecutive.active_employees} />
        <KpiCard label="Опубликованные графики" value={safeExecutive.published_assignments} />
        <KpiCard label="Среднее покрытие" value={`${safeExecutive.avg_coverage_percent}%`} />
        <KpiCard label="Интервалы с дефицитом" value={safeExecutive.gap_intervals_count} />
        <KpiCard label="SL/SLA Naumen" value={`${safeExecutive.avg_service_level_percent}%`} />
        <KpiCard label="АНТ" value={`${safeExecutive.avg_aht_sec} сек`} />
        <KpiCard label="Плановые часы" value={safeExecutive.planned_hours} />
        <KpiCard label="Фактические часы" value={safeExecutive.actual_hours} />
        <KpiCard label="Adherence" value={`${safeExecutive.adherence_percent}%`} />
        <KpiCard label="Последняя синхронизация NCC" value={String(nccLocal?.last_sync_at || "нет")} />
        <KpiCard label="Последний запуск генерации" value={lastGeneration ? String(lastGeneration.date_from) : "нет"} />
      </section>

      {!hasNccData ? (
        <SectionCard>
          <EmptyState
            title={String(nccLocal?.message || "Данные Naumen за выбранный период не загружены")}
            description={String(nccLocal?.partner_uuid ? "Для активного контура указан Naumen UUID, но локальная WFM БД пока не содержит NCC-статистику." : "Naumen/NCC не настроен для активного контура. Ручной режим статистики сохранён.")}
            action={nccLocal?.partner_uuid ? <AsyncButton type="button" onClick={syncFromNaumen} loading={syncing} loadingText="Загружаем из Naumen...">Загрузить из Naumen</AsyncButton> : null}
          />
        </SectionCard>
      ) : null}

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
