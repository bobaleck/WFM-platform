import { useEffect, useState } from "react";
import { getLocalNccOperatorWorkload, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";

export function OperatorWorkload() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [message, setMessage] = useState("Загрузка операторской нагрузки...");

  useEffect(() => {
    getLocalNccOperatorWorkload()
      .then((result) => {
        setRows(Array.isArray(result.items) ? result.items as AnyRecord[] : []);
        setMessage("Операторская нагрузка Naumen за выбранный период не загружена.");
      })
      .catch(() => setMessage("Не удалось загрузить локальную операторскую нагрузку."));
  }, []);

  return (
    <SectionCard title="Операторская нагрузка" description="Оператор/очередь/час из сохранённых данных Naumen/NCC.">
      {rows.length === 0 ? <EmptyState title={message} description="Загрузите данные Naumen/NCC для активного контура." /> : null}
      <DataTable columns={[
        { key: "interval_start", label: "Интервал", render: (row) => String(row.interval_start).replace("T", " ").slice(0, 16) },
        { key: "queue_name", label: "Очередь" },
        { key: "operator_login", label: "Оператор" },
        { key: "handled", label: "Обработано" },
        { key: "aht_sec", label: "АНТ" },
        { key: "talk_sec_total", label: "Разговор, сек" }
      ]} rows={rows} emptyText={message} />
    </SectionCard>
  );
}
