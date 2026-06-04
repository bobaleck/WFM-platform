import { useEffect, useState } from "react";
import { apiPost, apiPut } from "../api/client";
import { getList, type AnyRecord } from "../api/wfm";
import { DataTable, type Column } from "../components/DataTable";
import { SectionCard } from "../components/SectionCard";
import { ActionToolbar } from "../components/ActionToolbar";

type Props = {
  title: string;
  description: string;
  endpoint: string;
  columns: Column[];
  emptyText?: string;
  createLabel?: string;
  fields?: Array<{ key: string; label: string; type?: "text" | "number" | "time" | "textarea"; defaultValue?: string | number | boolean }>;
};

export function GenericTablePage({ title, description, endpoint, columns, emptyText, createLabel = "Создать", fields = [] }: Props) {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [editing, setEditing] = useState<AnyRecord | null>(null);
  const [form, setForm] = useState<AnyRecord>({});

  const load = () => getList(endpoint).then(setRows).catch(() => setError("Не удалось загрузить данные"));

  useEffect(() => {
    void load();
  }, [endpoint]);

  const openForm = (row?: AnyRecord) => {
    const base: AnyRecord = {};
    fields.forEach((field) => {
      base[field.key] = row?.[field.key] ?? field.defaultValue ?? "";
    });
    setEditing(row || {});
    setForm(base);
    setError("");
    setMessage("");
  };

  const save = async () => {
    try {
      const payload = { ...form };
      fields.forEach((field) => {
        if (field.type === "number") payload[field.key] = Number(payload[field.key] || 0);
      });
      if (editing?.id) {
        await apiPut(`${endpoint}/${editing.id}`, payload);
        setMessage("Изменения сохранены.");
      } else {
        await apiPost(endpoint, payload);
        setMessage("Запись создана.");
      }
      setEditing(null);
      await load();
    } catch {
      setError("Операция не выполнена. Проверьте заполнение формы и права доступа.");
    }
  };

  const archive = async (row: AnyRecord) => {
    try {
      await apiPost(`${endpoint}/${row.id}/archive`, {});
      setMessage("Запись архивирована.");
      await load();
    } catch {
      setError("Не удалось архивировать запись.");
    }
  };

  return (
    <SectionCard title={title} description={description}>
      <ActionToolbar>
        {fields.length ? <button type="button" onClick={() => openForm()}>{createLabel}</button> : null}
      </ActionToolbar>
      {message ? <p className="success-text">{message}</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
      {editing ? (
        <div className="form-grid">
          {fields.map((field) => (
            <div className="form-field" key={field.key}>
              <label>{field.label}</label>
              {field.type === "textarea" ? (
                <textarea value={String(form[field.key] ?? "")} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />
              ) : (
                <input type={field.type || "text"} value={String(form[field.key] ?? "")} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />
              )}
            </div>
          ))}
          <ActionToolbar>
            <button type="button" onClick={save}>Сохранить</button>
            <button className="secondary" type="button" onClick={() => setEditing(null)}>Отмена</button>
          </ActionToolbar>
        </div>
      ) : null}
      <DataTable columns={[
        ...columns,
        ...(fields.length ? [{ key: "actions", label: "Действия", render: (row: AnyRecord) => (
          <ActionToolbar>
            <button className="secondary" type="button" onClick={() => openForm(row)}>Редактировать</button>
            <button className="secondary" type="button" onClick={() => archive(row)}>Архивировать</button>
          </ActionToolbar>
        ) }] : [])
      ]} rows={rows} emptyText={emptyText} />
    </SectionCard>
  );
}
