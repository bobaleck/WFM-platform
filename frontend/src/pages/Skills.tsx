import { Fragment, useEffect, useMemo, useState } from "react";
import { apiPost, apiPut } from "../api/client";
import { endpoints, getList, type AnyRecord } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
import { SectionCard } from "../components/SectionCard";

const emptyForm = {
  name: "",
  description: "",
  is_active: true
};

export function Skills() {
  const [skills, setSkills] = useState<AnyRecord[]>([]);
  const [employees, setEmployees] = useState<AnyRecord[]>([]);
  const [skillEmployees, setSkillEmployees] = useState<Record<number, AnyRecord[]>>({});
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [assignSkillId, setAssignSkillId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [skillRows, employeeRows] = await Promise.all([getList(endpoints.skills), getList(endpoints.employees)]);
    setSkills(skillRows);
    setEmployees(employeeRows);
  }

  useEffect(() => {
    load().catch(() => setError("Не удалось загрузить навыки"));
  }, []);

  async function loadSkillEmployees(skillId: number) {
    const rows = await getList(`${endpoints.skills}/${skillId}/employees`);
    setSkillEmployees((current) => ({ ...current, [skillId]: rows }));
  }

  async function toggleExpand(skillId: number) {
    const next = expandedId === skillId ? null : skillId;
    setExpandedId(next);
    if (next) await loadSkillEmployees(next);
  }

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  }

  function openEdit(row: AnyRecord) {
    setEditingId(Number(row.id));
    setForm({ name: String(row.name || ""), description: String(row.description || ""), is_active: Boolean(row.is_active ?? true) });
    setShowForm(true);
  }

  async function saveSkill() {
    setMessage("");
    setError("");
    try {
      if (editingId) {
        await apiPut(`${endpoints.skills}/${editingId}`, form);
        setMessage("Навык обновлён.");
      } else {
        await apiPost(endpoints.skills, form);
        setMessage("Навык создан.");
      }
      setEditingId(null);
      setShowForm(false);
      setForm(emptyForm);
      await load();
    } catch {
      setError("Не удалось сохранить навык.");
    }
  }

  function openAssign(skillId: number) {
    setAssignSkillId(skillId);
    setSelectedIds((skillEmployees[skillId] || []).map((employee) => Number(employee.id)));
    setSearch("");
  }

  const assignCandidates = useMemo(() => {
    const query = search.trim().toLowerCase();
    return employees.filter((employee) => {
      const text = `${String(employee.full_name || "")} ${String(employee.inn || "")}`.toLowerCase();
      return !query || text.includes(query);
    });
  }, [employees, search]);

  function toggleSelected(employeeId: number) {
    setSelectedIds((current) => current.includes(employeeId) ? current.filter((id) => id !== employeeId) : [...current, employeeId]);
  }

  async function saveAssignments() {
    if (!assignSkillId) return;
    setMessage("");
    setError("");
    try {
      await apiPut(`${endpoints.skills}/${assignSkillId}/employees`, { employee_ids: selectedIds });
      setMessage("Назначения навыка сохранены.");
      await loadSkillEmployees(assignSkillId);
      setAssignSkillId(null);
    } catch {
      setError("Не удалось сохранить назначения навыка.");
    }
  }

  async function removeEmployeeSkill(skillId: number, employeeId: number) {
    setMessage("");
    setError("");
    try {
      const next = (skillEmployees[skillId] || []).map((employee) => Number(employee.id)).filter((id) => id !== employeeId);
      await apiPut(`${endpoints.skills}/${skillId}/employees`, { employee_ids: next });
      setMessage("Навык снят у сотрудника.");
      await loadSkillEmployees(skillId);
    } catch {
      setError("Не удалось снять навык у сотрудника.");
    }
  }

  return (
    <SectionCard title="Навыки" description="Навыки глобальные для всей WFM-платформы. Они назначаются сотрудникам и используются очередями и планировщиком.">
      {message ? <Alert>{message}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}
      <ActionToolbar><button type="button" onClick={openCreate}>Создать навык</button></ActionToolbar>

      {showForm ? (
        <div className="form-grid separated">
          <div className="form-field"><label>Название</label><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></div>
          <div className="form-field full"><label>Описание</label><input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></div>
          <label className="checkbox-field"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />Активен</label>
          <ActionToolbar><button type="button" onClick={saveSkill}>Сохранить</button><button className="secondary" type="button" onClick={() => { setEditingId(null); setShowForm(false); setForm(emptyForm); }}>Отмена</button></ActionToolbar>
        </div>
      ) : null}

      {skills.length === 0 ? <p className="muted-text">Создайте навыки вручную или загрузите их через реестр сотрудников.</p> : (
        <div className="table-wrap separated">
          <table className="data-table">
            <thead><tr><th>Название</th><th>Описание</th><th>Сотрудников</th><th>Статус</th><th>Действия</th></tr></thead>
            <tbody>
              {skills.map((skill) => {
                const skillId = Number(skill.id);
                const assigned = skillEmployees[skillId] || [];
                return (
                  <Fragment key={String(skill.id)}>
                    <tr>
                      <td>{String(skill.name || "")}</td>
                      <td>{String(skill.description || "")}</td>
                      <td>{String(skill.employee_count ?? assigned.length)}</td>
                      <td>{skill.is_active ? "Активен" : "Отключён"}</td>
                      <td><ActionToolbar><button className="secondary" type="button" onClick={() => openEdit(skill)}>Редактировать</button><button className="secondary" type="button" onClick={() => openAssign(skillId)}>Назначить сотрудникам</button><button className="secondary" type="button" onClick={() => toggleExpand(skillId)}>{expandedId === skillId ? "Скрыть" : "Сотрудники"}</button></ActionToolbar></td>
                    </tr>
                    {expandedId === skillId ? (
                      <tr key={`${String(skill.id)}-employees`}>
                        <td colSpan={5}>
                          <div className="diagnostic-result">
                            <h3>Сотрудники с навыком</h3>
                            {assigned.length === 0 ? <p className="muted-text">Навык пока никому не назначен.</p> : (
                              <table className="nested-table">
                                <thead><tr><th>ФИО</th><th>ИНН</th><th>Должность</th><th>Действия</th></tr></thead>
                                <tbody>{assigned.map((employee) => <tr key={String(employee.id)}><td>{String(employee.full_name || "")}</td><td>{String(employee.inn || "")}</td><td>{String(employee.position || "")}</td><td><button className="secondary" type="button" onClick={() => removeEmployeeSkill(skillId, Number(employee.id))}>Убрать навык</button></td></tr>)}</tbody>
                              </table>
                            )}
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {assignSkillId ? (
        <div className="modal-backdrop">
          <div className="modal-panel">
            <h3>Назначить навык сотрудникам</h3>
            <div className="form-field"><label>Поиск по ФИО или ИНН</label><input value={search} onChange={(event) => setSearch(event.target.value)} /></div>
            <div className="modal-list">
              {assignCandidates.length === 0 ? <p className="muted-text">Сотрудники не найдены.</p> : assignCandidates.map((employee) => (
                <label key={String(employee.id)} className="checkbox-field">
                  <input type="checkbox" checked={selectedIds.includes(Number(employee.id))} onChange={() => toggleSelected(Number(employee.id))} />
                  {String(employee.full_name || "")} {employee.inn ? `· ${String(employee.inn)}` : ""}
                </label>
              ))}
            </div>
            <ActionToolbar><button type="button" onClick={saveAssignments}>Сохранить</button><button className="secondary" type="button" onClick={() => setAssignSkillId(null)}>Отмена</button></ActionToolbar>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
