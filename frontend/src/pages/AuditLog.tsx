import { useEffect, useState } from "react";
import { getList, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";

export function AuditLogPage() {
  const [rows, setRows] = useState<AnyRecord[]>([]);

  useEffect(() => {
    getList("/api/v1/audit-log").then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <section className="panel">
      <div className="section-title">
        <div><h2>Журнал действий</h2><p>Последние действия пользователей и системные события.</p></div>
      </div>
      <DataTable columns={[
        { key: "created_at", label: "Дата", render: (row) => String(row.created_at).replace("T", " ").slice(0, 19) },
        { key: "actor", label: "Пользователь" },
        { key: "action", label: "Действие" },
        { key: "entity_type", label: "Объект" },
        { key: "entity_id", label: "ID" },
        { key: "details", label: "Детали" }
      ]} rows={rows} />
    </section>
  );
}
