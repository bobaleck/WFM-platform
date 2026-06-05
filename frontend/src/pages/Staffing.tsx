import { useEffect, useMemo, useState } from "react";
import { calculateStaffing, endpoints, getList, type AnyRecord } from "../api/wfm";
import { AsyncButton } from "../components/AsyncButton";
import { DataTable } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";

export function Staffing() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [settings, setSettings] = useState<AnyRecord | null>(null);
  const [dateFrom, setDateFrom] = useState("2026-01-15");
  const [dateTo, setDateTo] = useState("2026-01-21");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [calculating, setCalculating] = useState(false);

  const loadRows = () => getList(endpoints.staffing).then(setRows).catch(() => setError("Не удалось загрузить потребность"));

  useEffect(() => {
    loadRows();
    fetch(endpoints.planningSettings).then((response) => response.json()).then(setSettings).catch(() => setSettings(null));
  }, []);

  const totals = useMemo(() => {
    const required = rows.reduce((sum, row) => sum + Number(row.required_agents ?? 0), 0);
    const planned = rows.reduce((sum, row) => sum + Number(row.planned_agents ?? 0), 0);
    return { intervals: rows.length, required, planned, gap: planned - required };
  }, [rows]);

  const runCalculation = async () => {
    setError("");
    setMessage("");
    setCalculating(true);
    try {
      const result = await calculateStaffing(dateFrom, dateTo);
      setMessage(`Рассчитано интервалов: ${result.calculated_intervals}`);
      await loadRows();
    } catch {
      setError("Расчёт потребности не выполнен");
    } finally {
      setCalculating(false);
    }
  };

  return (
    <>
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Потребность</h2>
            <p>Потребность рассчитывает, сколько операторов требуется в каждом интервале, исходя из нагрузки, AHT, целевой занятости и резерва.</p>
          </div>
        </div>
        <p className="muted-text">Формула MVP: поступившие обращения умножаются на AHT, затем учитываются длительность интервала, целевая занятость и резерв на перерывы, обучение и невыходы.</p>
        <div className="form-row">
          <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          <AsyncButton type="button" onClick={runCalculation} loading={calculating} loadingText="Рассчитываем...">Рассчитать потребность</AsyncButton>
        </div>
        {rows.length === 0 ? <p className="muted-text">Сначала загрузите нагрузку, затем рассчитайте потребность. Если нагрузки нет за выбранный период, расчёт вернёт 0 интервалов.</p> : null}
        {settings ? (
          <div className="result-strip">
            <span>Метод: <strong>{String(settings.calculation_method || "MVP")}</strong></span>
            <span>Целевая занятость: <strong>{String(settings.target_occupancy ?? 0.85)}</strong></span>
            <span>Резерв: <strong>{String(settings.shrinkage_percent ?? 25)}%</strong></span>
          </div>
        ) : null}
        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>
      <section className="kpi-grid compact">
        <KpiCard label="Интервалов" value={totals.intervals} />
        <KpiCard label="Требуется операторов" value={totals.required} />
        <KpiCard label="Запланировано" value={totals.planned} />
        <KpiCard label="Дефицит" value={totals.gap} hint="отрицательное значение = дефицит" />
      </section>
      <section className="panel">
        <DataTable columns={[
          { key: "interval_start", label: "Начало", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
          { key: "queue_name", label: "Очередь" },
          { key: "required_agents", label: "Требуется" },
          { key: "planned_agents", label: "Запланировано" },
          { key: "coverage", label: "Покрытие", render: (row) => `${Number(row.required_agents) ? Math.round(Number(row.planned_agents ?? 0) / Number(row.required_agents) * 100) : 0}%` },
          { key: "gap_agents", label: "Дефицит/избыток", render: (row) => <span className={Number(row.gap_agents) < 0 ? "negative" : "positive"}>{String(row.gap_agents)}</span> },
          { key: "calculation_note", label: "Комментарий" }
        ]} rows={rows} emptyText="Сначала загрузите нагрузку, затем рассчитайте потребность." />
      </section>
    </>
  );
}
