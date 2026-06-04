import { useEffect, useState } from "react";
import { confirmPeriod, downloadCsv, endpoints, generateDraftSchedule, getList, publishPeriod, recalculateCoverage, updateScheduleStatus, type AnyRecord } from "../api/wfm";
import { Alert } from "../components/Alert";
import { DataTable } from "../components/DataTable";
import { DateRangeFilter } from "../components/DateRangeFilter";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

const scheduleStatusLabels: Record<string, string> = {
  draft: "Черновик",
  planned: "Запланировано",
  confirmed: "Подтверждено",
  published: "Опубликовано",
  cancelled: "Отменено"
};

const recommendationTypeLabels: Record<string, string> = {
  skill_gap: "Не хватает навыка",
  coverage_gap: "Дефицит покрытия",
  overtime_risk: "Риск переработки",
  absence_conflict: "Конфликт с отсутствием",
  fairness_warning: "Баланс распределения"
};

const severityLabels: Record<string, string> = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
  critical: "Критичная"
};

export function Schedules() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [coverage, setCoverage] = useState<AnyRecord[]>([]);
  const [recommendations, setRecommendations] = useState<AnyRecord[]>([]);
  const [recommendationType, setRecommendationType] = useState("");
  const [dateFrom, setDateFrom] = useState("2026-01-15");
  const [dateTo, setDateTo] = useState("2026-01-21");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  const loadRows = () => getList(endpoints.schedules).then(setRows).catch(() => setError("Не удалось загрузить графики"));
  const loadCoverage = () => getList(endpoints.coverage).then(setCoverage).catch(() => setCoverage([]));
  const loadRecommendations = () => getList(`${endpoints.recommendations}${recommendationType ? `?recommendation_type=${recommendationType}` : ""}`).then(setRecommendations).catch(() => setRecommendations([]));

  useEffect(() => {
    loadRows();
    loadCoverage();
    loadRecommendations();
  }, [recommendationType]);

  const runAction = async (action: () => Promise<AnyRecord>, success: (result: AnyRecord) => string) => {
    setError("");
    setMessage("");
    try {
      const result = await action();
      setMessage(success(result));
      await loadRows();
      await loadCoverage();
      await loadRecommendations();
    } catch {
      setError("Действие не выполнено");
    }
  };

  const changeStatus = async (id: number, action: "confirm" | "publish" | "cancel") => {
    await updateScheduleStatus(id, action);
    await loadRows();
    await loadCoverage();
  };
  const exportFile = async (path: string, prefix: string) => {
    setError("");
    setMessage("");
    setExporting(true);
    try {
      await downloadCsv(path, `${prefix}_${new Date().toISOString().slice(0, 10)}.csv`);
      setMessage("Файл выгружен");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Выгрузка не выполнена");
    } finally {
      setExporting(false);
    }
  };

  return (
    <>
      <SectionCard title="Графики смен" description="Черновые, подтверждённые и опубликованные назначения с покрытием по интервалам.">
        <p className="muted-text">Как пользоваться: заполните сотрудников, команды, смены и нагрузку вручную или реестрами, рассчитайте потребность, сформируйте черновик, проверьте покрытие, подтвердите и опубликуйте график.</p>
        {rows.length === 0 ? <p className="muted-text">Недостающие данные: проект, сотрудники, смены/расписание, нагрузка или рассчитанная потребность. Заполните их перед генерацией графика.</p> : null}
        <div className="form-row">
          <DateRangeFilter dateFrom={dateFrom} dateTo={dateTo} onDateFrom={setDateFrom} onDateTo={setDateTo} />
          <button type="button" onClick={() => runAction(() => generateDraftSchedule(dateFrom, dateTo), (result) => `Создано: ${result.created_assignments}, дефицитов: ${result.coverage_gaps}`)}>Сформировать черновик</button>
          <button type="button" onClick={() => runAction(() => confirmPeriod(dateFrom, dateTo), (result) => `Подтверждено: ${result.confirmed}`)}>Подтвердить период</button>
          <button type="button" onClick={() => runAction(() => publishPeriod(dateFrom, dateTo), (result) => `Опубликовано: ${result.published}`)}>Опубликовать период</button>
          <button type="button" className="secondary" onClick={() => runAction(() => recalculateCoverage(dateFrom, dateTo), (result) => `Покрытие пересчитано: ${result.recalculated_intervals}`)}>Пересчитать покрытие</button>
          <button type="button" className="secondary" disabled={exporting} onClick={() => exportFile("/api/v1/schedules/export.csv", "schedules")}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>
        </div>
        {message ? <Alert>{message}</Alert> : null}
        {error ? <Alert type="error">{error}</Alert> : null}
      </SectionCard>
      <SectionCard title="Назначения" description="Рабочий список смен и статусов публикации.">
        <DataTable columns={[
          { key: "work_date", label: "Дата" },
          { key: "employee_name", label: "Сотрудник" },
          { key: "shift_name", label: "Смена" },
          { key: "queue_name", label: "Очередь" },
          { key: "status", label: "Статус", render: (row) => <StatusBadge value={scheduleStatusLabels[String(row.status)] || "Не указан"} /> },
          { key: "note", label: "Примечание" },
          { key: "actions", label: "Действия", render: (row) => (
            <div className="actions">
              {row.status === "draft" ? <button type="button" onClick={() => changeStatus(Number(row.id), "confirm")}>Подтвердить</button> : null}
              {row.status === "confirmed" ? <button type="button" onClick={() => changeStatus(Number(row.id), "publish")}>Опубликовать</button> : null}
              {row.status !== "cancelled" ? <button type="button" className="secondary" onClick={() => changeStatus(Number(row.id), "cancel")}>Отменить</button> : null}
            </div>
          ) }
        ]} rows={rows} />
      </SectionCard>
      <SectionCard title="Рекомендации планировщика" description="MVP scoring algorithm фиксирует дефициты навыков, покрытия и риски распределения.">
        <div className="form-row">
          <select value={recommendationType} onChange={(event) => setRecommendationType(event.target.value)}>
            <option value="">Все типы</option>
            <option value="skill_gap">Не хватает навыка</option>
            <option value="coverage_gap">Дефицит покрытия</option>
            <option value="overtime_risk">Риск переработки</option>
            <option value="absence_conflict">Конфликт с отсутствием</option>
            <option value="fairness_warning">Баланс распределения</option>
          </select>
          <button type="button" className="secondary" onClick={loadRecommendations}>Обновить</button>
        </div>
        <DataTable columns={[
          { key: "work_date", label: "Дата" },
          { key: "queue_name", label: "Очередь" },
          { key: "recommendation_type", label: "Тип", render: (row) => recommendationTypeLabels[String(row.recommendation_type)] || "Рекомендация" },
          { key: "severity", label: "Важность", render: (row) => <StatusBadge value={severityLabels[String(row.severity)] || "Средняя"} /> },
          { key: "message", label: "Рекомендация" }
        ]} rows={recommendations} />
      </SectionCard>
      <SectionCard title="Покрытие" description="Сравнение потребности с черновыми, подтверждёнными и опубликованными назначениями." actions={<button type="button" onClick={() => exportFile("/api/v1/coverage/export.csv", "coverage")} disabled={exporting}>{exporting ? "Выгрузка..." : "Выгрузить"}</button>}>
        <DataTable columns={[
          { key: "interval_start", label: "Интервал", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
          { key: "queue_name", label: "Очередь" },
          { key: "required_agents", label: "Требуется" },
          { key: "planned_agents", label: "План" },
          { key: "confirmed_agents", label: "Подтверждено" },
          { key: "published_agents", label: "Опубликовано" },
          { key: "gap_agents", label: "Дефицит", render: (row) => <span className={Number(row.gap_agents) > 0 ? "negative" : "positive"}>{String(row.gap_agents)}</span> },
          { key: "coverage_percent", label: "Покрытие", render: (row) => `${row.coverage_percent}%` }
        ]} rows={coverage} />
      </SectionCard>
    </>
  );
}
