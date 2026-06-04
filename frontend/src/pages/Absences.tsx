import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiPost, apiPut } from "../api/client";
import { endpoints, getList, type AnyRecord } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
import { SectionCard } from "../components/SectionCard";

const typeLabels: Record<string, string> = {
  vacation: "Отпуск",
  sick_leave: "Больничный",
  training: "Обучение",
  day_off: "Отгул",
  other: "Прочее"
};

const statusLabels: Record<string, string> = {
  planned: "Запланировано",
  confirmed: "Подтверждено",
  cancelled: "Отменено"
};

const emptyForm = {
  employee_id: "",
  absence_type: "vacation",
  date_from: "",
  date_to: "",
  status: "planned",
  comment: ""
};

export function Absences() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [employees, setEmployees] = useState<AnyRecord[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [absenceRows, employeeRows] = await Promise.all([getList(endpoints.absences), getList(endpoints.employees)]);
    setRows(absenceRows);
    setEmployees(employeeRows);
  }

  useEffect(() => {
    load().catch(() => setError("Не удалось загрузить отсутствия"));
  }, []);

  const employeeOptions = useMemo(() => {
    const query = search.trim().toLowerCase();
    return employees.filter((employee) => {
      const text = `${String(employee.full_name || "")} ${String(employee.inn || "")}`.toLowerCase();
      return !query || text.includes(query);
    });
  }, [employees, search]);

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setSearch("");
    setShowForm(true);
  }

  function openEdit(row: AnyRecord) {
    setEditingId(Number(row.id));
    setForm({
      employee_id: String(row.employee_id || ""),
      absence_type: String(row.absence_type || "vacation"),
      date_from: String(row.date_from || ""),
      date_to: String(row.date_to || ""),
      status: String(row.status || "planned"),
      comment: String(row.comment || "")
    });
    setSearch(String(row.employee_name || ""));
    setShowForm(true);
  }

  async function saveAbsence() {
    setMessage("");
    setError("");
    try {
      const payload = { ...form, employee_id: Number(form.employee_id) };
      if (editingId) {
        await apiPut(`${endpoints.absences}/${editingId}`, payload);
        setMessage("Отсутствие обновлено.");
      } else {
        await apiPost(endpoints.absences, payload);
        setMessage("Отсутствие создано.");
      }
      setEditingId(null);
      setShowForm(false);
      setForm(emptyForm);
      await load();
    } catch {
      setError("Не удалось сохранить отсутствие. Выберите сотрудника активного проекта и корректный период.");
    }
  }

  async function cancelAbsence(row: AnyRecord) {
    setMessage("");
    setError("");
    try {
      await apiPost(`${endpoints.absences}/${row.id}/cancel`, {});
      setMessage("Отсутствие отменено.");
      await load();
    } catch {
      setError("Не удалось отменить отсутствие.");
    }
  }

  async function deleteAbsence(row: AnyRecord) {
    if (!window.confirm("Удалить отсутствие из WFM?")) return;
    setMessage("");
    setError("");
    try {
      await apiDelete(`${endpoints.absences}/${row.id}`);
      setMessage("Отсутствие удалено.");
      await load();
    } catch {
      setError("Не удалось удалить отсутствие.");
    }
  }

  return (
    <SectionCard title="Отсутствия" description="Отсутствия ведутся вручную и используются планировщиком, чтобы не назначать сотрудника на смену в дни отпуска, больничного, обучения или отгула.">
      {message ? <Alert>{message}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}
      <ActionToolbar><button type="button" onClick={openCreate}>Создать отсутствие</button></ActionToolbar>

      {showForm ? (
        <div className="form-grid separated">
          <div className="form-field full">
            <label>Сотрудник</label>
            <input placeholder="Поиск по ФИО или ИНН" value={search} onChange={(event) => setSearch(event.target.value)} />
            <select value={form.employee_id} onChange={(event) => setForm({ ...form, employee_id: event.target.value })}>
              <option value="">Выберите сотрудника</option>
              {employeeOptions.map((employee) => <option key={String(employee.id)} value={String(employee.id)}>{String(employee.full_name || "")}{employee.inn ? ` · ${String(employee.inn)}` : ""}</option>)}
            </select>
          </div>
          <div className="form-field"><label>Тип отсутствия</label><select value={form.absence_type} onChange={(event) => setForm({ ...form, absence_type: event.target.value })}>{Object.entries(typeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          <div className="form-field"><label>Дата начала</label><input type="date" value={form.date_from} onChange={(event) => setForm({ ...form, date_from: event.target.value })} /></div>
          <div className="form-field"><label>Дата окончания</label><input type="date" value={form.date_to} onChange={(event) => setForm({ ...form, date_to: event.target.value })} /></div>
          <div className="form-field"><label>Статус</label><select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>{Object.entries(statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          <div className="form-field full"><label>Комментарий</label><input value={form.comment} onChange={(event) => setForm({ ...form, comment: event.target.value })} /></div>
          <ActionToolbar><button type="button" onClick={saveAbsence}>Сохранить</button><button className="secondary" type="button" onClick={() => { setShowForm(false); setEditingId(null); setForm(emptyForm); }}>Отмена</button></ActionToolbar>
        </div>
      ) : null}

      {rows.length === 0 ? <p className="muted-text">Создайте отсутствия вручную, чтобы планировщик не назначал сотрудников в эти дни.</p> : (
        <div className="table-wrap separated">
          <table className="data-table">
            <thead><tr><th>Сотрудник</th><th>Тип</th><th>Дата начала</th><th>Дата окончания</th><th>Статус</th><th>Комментарий</th><th>Действия</th></tr></thead>
            <tbody>{rows.map((row) => <tr key={String(row.id)}><td>{String(row.employee_name || "")}</td><td>{typeLabels[String(row.absence_type)] || "Прочее"}</td><td>{String(row.date_from || "")}</td><td>{String(row.date_to || "")}</td><td>{statusLabels[String(row.status)] || "Запланировано"}</td><td>{String(row.comment || "")}</td><td><ActionToolbar><button className="secondary" type="button" onClick={() => openEdit(row)}>Редактировать</button><button className="secondary" type="button" onClick={() => cancelAbsence(row)}>Отменить</button><button className="secondary" type="button" onClick={() => deleteAbsence(row)}>Удалить</button></ActionToolbar></td></tr>)}</tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
