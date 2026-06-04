import { Fragment, useEffect, useMemo, useState } from "react";
import { apiPost, apiPut } from "../api/client";
import { endpoints, getList, type AnyRecord } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";

const emptyForm = {
  name: "",
  supervisor_name: "",
  description: "",
  is_active: true
};

function oneCLabel(row: AnyRecord) {
  const value = String(row.onec_status || "not_checked");
  if (value === "working") return "Работает";
  if (value === "dismissed") return "Уволен";
  if (value === "not_found") return "Не найден в 1С";
  if (value === "not_checked") return "Не проверялся";
  return "Ошибка сверки";
}

function naumenLabel(row: AnyRecord) {
  const value = String(row.naumen_status || "not_linked");
  if (value === "linked") return "Сопоставлен";
  if (value === "not_linked") return "Не сопоставлен";
  if (value === "not_found") return "Не найден в Naumen";
  if (value === "mismatch") return "Требует выбора";
  return "Ошибка сверки";
}

export function Teams() {
  const [teams, setTeams] = useState<AnyRecord[]>([]);
  const [employees, setEmployees] = useState<AnyRecord[]>([]);
  const [memberRows, setMemberRows] = useState<Record<number, AnyRecord[]>>({});
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [addTeamId, setAddTeamId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const [teamRows, employeeRows] = await Promise.all([getList(endpoints.teams), getList(endpoints.employees)]);
    setTeams(teamRows);
    setEmployees(employeeRows);
  }

  useEffect(() => {
    load().catch(() => setError("Не удалось загрузить команды"));
  }, []);

  async function loadMembers(teamId: number) {
    const rows = await getList(`${endpoints.teams}/${teamId}/employees`);
    setMemberRows((current) => ({ ...current, [teamId]: rows }));
  }

  async function toggleExpand(teamId: number) {
    const next = expandedId === teamId ? null : teamId;
    setExpandedId(next);
    if (next) await loadMembers(next);
  }

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setShowForm(true);
  }

  function openEdit(row: AnyRecord) {
    setEditingId(Number(row.id));
    setForm({
      name: String(row.name || ""),
      supervisor_name: String(row.supervisor_name || ""),
      description: String(row.description || ""),
      is_active: Boolean(row.is_active ?? true)
    });
    setShowForm(true);
  }

  async function saveTeam() {
    setMessage("");
    setError("");
    try {
      if (editingId) {
        await apiPut(`${endpoints.teams}/${editingId}`, form);
        setMessage("Команда обновлена.");
      } else {
        await apiPost(endpoints.teams, form);
        setMessage("Команда создана.");
      }
      setEditingId(null);
      setShowForm(false);
      setForm(emptyForm);
      await load();
    } catch {
      setError("Не удалось сохранить команду.");
    }
  }

  function openAddMembers(teamId: number) {
    setAddTeamId(teamId);
    setSelectedIds([]);
    setSearch("");
  }

  const addCandidates = useMemo(() => {
    if (!addTeamId) return [];
    const current = new Set((memberRows[addTeamId] || []).map((row) => Number(row.id)));
    const query = search.trim().toLowerCase();
    return employees.filter((employee) => {
      if (current.has(Number(employee.id))) return false;
      const text = `${String(employee.full_name || "")} ${String(employee.inn || "")}`.toLowerCase();
      return !query || text.includes(query);
    });
  }, [addTeamId, employees, memberRows, search]);

  async function saveAddedMembers() {
    if (!addTeamId) return;
    setMessage("");
    setError("");
    try {
      const current = (memberRows[addTeamId] || []).map((row) => Number(row.id));
      await apiPut(`${endpoints.teams}/${addTeamId}/employees`, { employee_ids: Array.from(new Set([...current, ...selectedIds])) });
      setMessage("Участники добавлены.");
      setAddTeamId(null);
      await loadMembers(addTeamId);
      await load();
    } catch {
      setError("Не удалось добавить участников. В команду можно добавлять только сотрудников текущего проекта.");
    }
  }

  async function removeMember(teamId: number, employeeId: number) {
    setMessage("");
    setError("");
    try {
      const next = (memberRows[teamId] || []).map((row) => Number(row.id)).filter((id) => id !== employeeId);
      await apiPut(`${endpoints.teams}/${teamId}/employees`, { employee_ids: next });
      setMessage("Сотрудник убран из команды.");
      await loadMembers(teamId);
      await load();
    } catch {
      setError("Не удалось изменить состав команды.");
    }
  }

  function toggleSelected(employeeId: number) {
    setSelectedIds((current) => current.includes(employeeId) ? current.filter((id) => id !== employeeId) : [...current, employeeId]);
  }

  return (
    <SectionCard title="Команды" description="Команды принадлежат текущему рабочему контуру. В состав можно добавить только сотрудников, доступных в этом контуре.">
      {message ? <Alert>{message}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}
      <ActionToolbar><button type="button" onClick={openCreate}>Создать команду</button></ActionToolbar>

      {showForm ? (
        <div className="form-grid separated">
          <div className="form-field"><label>Название</label><input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></div>
          <div className="form-field"><label>Супервайзер</label><input value={form.supervisor_name} onChange={(event) => setForm({ ...form, supervisor_name: event.target.value })} /></div>
          <div className="form-field full"><label>Описание</label><input value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></div>
          <label className="checkbox-field"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />Активна</label>
          <ActionToolbar><button type="button" onClick={saveTeam}>Сохранить</button><button className="secondary" type="button" onClick={() => { setEditingId(null); setShowForm(false); setForm(emptyForm); }}>Отмена</button></ActionToolbar>
        </div>
      ) : null}

      {teams.length === 0 ? <p className="muted-text">Создайте команды вручную или загрузите сотрудников с командами через реестр.</p> : (
        <div className="table-wrap separated">
          <table className="data-table">
            <thead><tr><th>Название</th><th>Супервайзер</th><th>Участников</th><th>Статус</th><th>Действия</th></tr></thead>
            <tbody>
              {teams.map((team) => {
                const teamId = Number(team.id);
                const currentMembers = memberRows[teamId] || [];
                return (
                  <Fragment key={String(team.id)}>
                    <tr>
                      <td>{String(team.name || "")}</td>
                      <td>{String(team.supervisor_name || "")}</td>
                      <td>{String(team.employee_count ?? currentMembers.length)}</td>
                      <td>{team.is_active ? "Активна" : "Отключена"}</td>
                      <td><ActionToolbar><button className="secondary" type="button" onClick={() => openEdit(team)}>Редактировать</button><button className="secondary" type="button" onClick={() => toggleExpand(teamId)}>{expandedId === teamId ? "Скрыть состав" : "Состав"}</button></ActionToolbar></td>
                    </tr>
                    {expandedId === teamId ? (
                      <tr key={`${String(team.id)}-members`}>
                        <td colSpan={5}>
                          <div className="diagnostic-result">
                            <ActionToolbar><h3>Состав команды</h3><button className="secondary" type="button" onClick={() => openAddMembers(teamId)}>Добавить участников</button></ActionToolbar>
                            {currentMembers.length === 0 ? <p className="muted-text">В команде пока нет сотрудников.</p> : (
                              <table className="nested-table">
                                <thead><tr><th>ФИО</th><th>ИНН</th><th>Должность</th><th>1С</th><th>Naumen</th><th>Действия</th></tr></thead>
                                <tbody>{currentMembers.map((employee) => <tr key={String(employee.id)}><td>{String(employee.full_name || "")}</td><td>{String(employee.inn || "")}</td><td>{String(employee.position || "")}</td><td><StatusBadge value={oneCLabel(employee)} /></td><td><StatusBadge value={naumenLabel(employee)} /></td><td><button className="secondary" type="button" onClick={() => removeMember(teamId, Number(employee.id))}>Убрать из команды</button></td></tr>)}</tbody>
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

      {addTeamId ? (
        <div className="modal-backdrop">
          <div className="modal-panel">
            <h3>Добавить участников команды</h3>
            <div className="form-field"><label>Поиск по ФИО или ИНН</label><input value={search} onChange={(event) => setSearch(event.target.value)} /></div>
            <div className="modal-list">
              {addCandidates.length === 0 ? <p className="muted-text">Подходящих сотрудников нет.</p> : addCandidates.map((employee) => (
                <label key={String(employee.id)} className="checkbox-field">
                  <input type="checkbox" checked={selectedIds.includes(Number(employee.id))} onChange={() => toggleSelected(Number(employee.id))} />
                  {String(employee.full_name || "")} {employee.inn ? `· ${String(employee.inn)}` : ""}
                </label>
              ))}
            </div>
            <ActionToolbar><button type="button" onClick={saveAddedMembers}>Добавить</button><button className="secondary" type="button" onClick={() => setAddTeamId(null)}>Отмена</button></ActionToolbar>
          </div>
        </div>
      ) : null}
    </SectionCard>
  );
}
