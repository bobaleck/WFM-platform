import { useEffect, useState } from "react";
import { downloadWorkloadTemplate, endpoints, getCurrentContour, getList, getLocalNccLoad, syncContourNaumen, uploadWorkloadCsvNew, uploadWorkloadXlsx, type AnyRecord } from "../api/wfm";
import { AsyncButton } from "../components/AsyncButton";
import { DataTable } from "../components/DataTable";
import { KpiCard } from "../components/KpiCard";

export function Workload() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [xlsxFile, setXlsxFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<AnyRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [syncingNaumen, setSyncingNaumen] = useState(false);
  const [totals, setTotals] = useState<AnyRecord>({});

  const loadRows = async () => {
    const local = await getLocalNccLoad().catch(() => null);
    if (local && Array.isArray(local.items)) {
      setRows(local.items as AnyRecord[]);
      setTotals((local.totals || {}) as AnyRecord);
      return;
    }
    await getList(endpoints.workload).then(setRows).catch(() => setError("Не удалось загрузить нагрузку"));
  };

  useEffect(() => {
    loadRows();
  }, []);

  const submitImport = async (type: "csv" | "xlsx") => {
    const file = type === "csv" ? csvFile : xlsxFile;
    if (!file) {
      setError(type === "csv" ? "Выберите CSV-файл" : "Выберите XLSX-файл");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = type === "csv" ? await uploadWorkloadCsvNew(file) : await uploadWorkloadXlsx(file);
      setImportResult(result);
      await loadRows();
    } catch {
      setError("Импорт нагрузки не выполнен");
    } finally {
      setLoading(false);
    }
  };

  const syncFromNaumen = async () => {
    setSyncingNaumen(true);
    setError("");
    try {
      const current = await getCurrentContour();
      if (!current) throw new Error("Контур не выбран");
      const end = new Date();
      end.setDate(end.getDate() + 1);
      const begin = new Date(end);
      begin.setDate(begin.getDate() - 7);
      const result = await syncContourNaumen(current.id, begin.toISOString().slice(0, 10), end.toISOString().slice(0, 10));
      const rowsByType = (result.rows_by_type || {}) as Record<string, number>;
      setImportResult({ status: result.status, rows_total: rowsByType.load ?? 0, rows_success: rowsByType.load ?? 0, rows_failed: 0 });
      await loadRows();
    } catch {
      setError("Автоматическая загрузка из Naumen/NCC не выполнена. Проверьте UUID Naumen/NCC активного контура и env backend.");
    } finally {
      setSyncingNaumen(false);
    }
  };

  return (
    <>
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Нагрузка</h2>
            <p>Нагрузка — интервальная статистика контакт-центра: поступившие, обработанные, потерянные обращения, AHT и SLA по очередям и периодам.</p>
          </div>
        </div>
        <p className="muted-text">Загрузите интервальную нагрузку по очередям. На её основе система рассчитает, сколько операторов требуется по интервалам.</p>
        <div className="form-row">
          <button type="button" className="secondary" onClick={() => downloadWorkloadTemplate().catch(() => setError("Не удалось скачать шаблон нагрузки."))}>Скачать шаблон</button>
          <input type="file" accept=".xlsx" onChange={(event) => setXlsxFile(event.target.files?.[0] ?? null)} />
          <button type="button" onClick={() => submitImport("xlsx")} disabled={loading}>{loading ? "Загрузка..." : "Загрузить реестр"}</button>
          <input type="file" accept=".csv,text/csv" onChange={(event) => setCsvFile(event.target.files?.[0] ?? null)} />
          <button type="button" className="secondary" onClick={() => submitImport("csv")} disabled={loading}>{loading ? "Загрузка..." : "Загрузить файл"}</button>
          <AsyncButton type="button" className="secondary" onClick={syncFromNaumen} loading={syncingNaumen} loadingText="Загружаем из Naumen...">Загрузить из Naumen/NCC</AsyncButton>
        </div>
        <p className="muted-text">Если UUID Naumen/NCC или env backend не заполнены, используйте ручную загрузку XLSX/CSV.</p>
        {error ? <p className="error-text">{error}</p> : null}
        {importResult ? (
          <div className="result-strip">
            <span>Всего строк: <strong>{String(importResult.rows_total)}</strong></span>
            <span>Успешно: <strong>{String(importResult.rows_success)}</strong></span>
            <span>Ошибок: <strong>{String(importResult.rows_failed)}</strong></span>
            <span>Статус: <strong>{String(importResult.status)}</strong></span>
          </div>
        ) : null}
      </section>
      <section className="kpi-grid compact">
        <KpiCard label="Поступило" value={String(totals.offered ?? 0)} />
        <KpiCard label="Обработано" value={String(totals.handled ?? 0)} />
        <KpiCard label="Потеряно" value={String(totals.lost ?? 0)} />
        <KpiCard label="Lost rate" value={`${String(totals.lost_rate ?? 0)}%`} />
        <KpiCard label="Средний АНТ" value={`${String(totals.aht_sec ?? 0)} сек`} />
        <KpiCard label="Средний SL" value={`${String(totals.sl_percent ?? 0)}%`} />
      </section>
      <section className="panel">
        <DataTable columns={[
          { key: "interval_start", label: "Начало", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
          { key: "queue_name", label: "Очередь" },
          { key: "offered", label: "Поступило", render: (row) => String(row.offered ?? row.offered_contacts ?? 0) },
          { key: "handled", label: "Обработано", render: (row) => String(row.handled ?? row.handled_contacts ?? 0) },
          { key: "lost", label: "Потеряно", render: (row) => String(row.lost ?? row.abandoned_contacts ?? 0) },
          { key: "lost_rate", label: "Lost rate", render: (row) => `${String(row.lost_rate ?? 0)}%` },
          { key: "aht_sec", label: "АНТ", render: (row) => String(row.aht_sec ?? row.average_handle_time_sec ?? 0) },
          { key: "sl_percent", label: "SL", render: (row) => `${String(row.sl_percent ?? row.service_level_percent ?? 0)}%` }
        ]} rows={rows} emptyText="Данные Naumen за выбранный период не загружены. Используйте кнопку «Загрузить из Naumen/NCC» или ручной XLSX/CSV." />
      </section>
    </>
  );
}
