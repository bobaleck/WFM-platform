import { useEffect, useState } from "react";
import { downloadWorkloadTemplate, endpoints, getList, uploadWorkloadCsvNew, uploadWorkloadXlsx, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";

export function Workload() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [xlsxFile, setXlsxFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<AnyRecord | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const loadRows = () => getList(endpoints.workload).then(setRows).catch(() => setError("Не удалось загрузить нагрузку"));

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
          <button type="button" className="secondary" disabled title="Endpoint интервальной статистики Naumen не подтверждён документацией. Используйте ручную загрузку.">Загрузить из Naumen</button>
        </div>
        <p className="muted-text">Автоматическая загрузка нагрузки из Naumen пока не настроена: endpoint не подтверждён документацией. Используйте ручную загрузку XLSX/CSV.</p>
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
      <section className="panel">
        <DataTable columns={[
          { key: "interval_start", label: "Начало", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
          { key: "queue_name", label: "Очередь" },
          { key: "offered_contacts", label: "Поступило" },
          { key: "handled_contacts", label: "Обработано" },
          { key: "abandoned_contacts", label: "Потеряно" },
          { key: "average_handle_time_sec", label: "AHT" },
          { key: "service_level_percent", label: "SL", render: (row) => `${row.service_level_percent}%` }
        ]} rows={rows} emptyText="Загрузите интервальную нагрузку через XLSX или CSV." />
      </section>
    </>
  );
}
