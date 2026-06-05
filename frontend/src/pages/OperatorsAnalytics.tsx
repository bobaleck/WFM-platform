import { useEffect, useState } from "react";
import { getLocalNccOperators, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";

export function OperatorsAnalytics() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [message, setMessage] = useState("Загрузка статистики операторов...");

  useEffect(() => {
    getLocalNccOperators()
      .then((result) => {
        setRows(Array.isArray(result.items) ? result.items as AnyRecord[] : []);
        setMessage("Данные Naumen за выбранный период не загружены.");
      })
      .catch(() => setMessage("Не удалось загрузить локальную статистику операторов."));
  }, []);

  return (
    <SectionCard title="Статистика операторов" description="Фактические обработчики активного контура из сохранённых данных Naumen/NCC.">
      {rows.length === 0 ? <EmptyState title={message} description="Запустите синхронизацию Naumen/NCC в настройках или на страницах аналитики." /> : null}
      <DataTable columns={[
        { key: "employee_uuid", label: "UUID" },
        { key: "login", label: "Login" },
        { key: "employee_title", label: "ФИО" },
        { key: "queues", label: "Очереди" },
        { key: "handled_calls_count", label: "Обработано" },
        { key: "avg_talk_sec", label: "АНТ" },
        { key: "sl_percent", label: "SL", render: (row) => `${String(row.sl_percent ?? 0)}%` },
        { key: "statuses_seen", label: "Статусы" },
        { key: "skills", label: "Навыки" }
      ]} rows={rows} emptyText={message} />
    </SectionCard>
  );
}
