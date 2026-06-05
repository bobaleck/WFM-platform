import { useEffect, useState } from "react";
import { getLocalNccForecastProfile, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";

export function ForecastProfile() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [message, setMessage] = useState("Загрузка профиля нагрузки...");

  useEffect(() => {
    getLocalNccForecastProfile()
      .then((result) => {
        setRows(Array.isArray(result.items) ? result.items as AnyRecord[] : []);
        setMessage("Профиль нагрузки Naumen за выбранный период не загружен.");
      })
      .catch(() => setMessage("Не удалось загрузить локальный профиль нагрузки."));
  }, []);

  return (
    <SectionCard title="Профиль нагрузки / Прогноз" description="Средние значения по дню недели, часу и очереди из сохранённых данных Naumen/NCC.">
      {rows.length === 0 ? <EmptyState title={message} description="Запустите синхронизацию Naumen/NCC для активного контура." /> : null}
      <DataTable columns={[
        { key: "weekday_name", label: "День" },
        { key: "hour_num", label: "Час" },
        { key: "queue_name", label: "Очередь" },
        { key: "avg_offered", label: "Среднее поступило" },
        { key: "avg_handled", label: "Среднее обработано" },
        { key: "avg_lost", label: "Среднее потеряно" },
        { key: "avg_aht_sec", label: "АНТ" },
        { key: "avg_sl_percent", label: "SL", render: (row) => `${String(row.avg_sl_percent ?? 0)}%` }
      ]} rows={rows} emptyText={message} />
    </SectionCard>
  );
}
