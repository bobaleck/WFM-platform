import { Fragment, useEffect, useRef, useState } from "react";
import { Alert } from "../components/Alert";
import { ActionToolbar } from "../components/ActionToolbar";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { apiDelete, apiPost, apiPut } from "../api/client";
import { checkAllEmployeesNaumen, checkAllEmployeesOneC, checkEmployeeNaumen, checkEmployeeNaumenUuid, checkEmployeeOneC, downloadEmployeeTemplate, endpoints, getContours, getList, updateEmployeeSkills, uploadEmployeeRegistry, type AnyRecord, type Contour } from "../api/wfm";

const emptyForm = {
  full_name: "",
  inn: "",
  birth_date: "",
  email: "",
  phone: "",
  position: "",
  team_id: "",
  skill_ids: [] as number[],
  project_ids: [] as number[],
  naumen_uuid: "",
  employment_type: "full_time",
  timezone: "Europe/Moscow",
  employment_status: "working",
  comment: "",
  is_active: true
};

const oneCLabels: Record<string, string> = {
  not_checked: "Не проверялся",
  working: "Работает",
  dismissed: "Уволен",
  not_found: "Не найден в 1С",
  not_found_person_cards: "Ошибка сверки",
  check_error: "Ошибка сверки",
  gateway_unavailable: "Ошибка сверки",
  gateway_invalid: "Ошибка сверки",
  gateway_timeout: "Ошибка сверки",
  onec_connection_error: "Ошибка сверки"
};

const naumenLabels: Record<string, string> = {
  not_linked: "Не сопоставлен",
  linked: "Сопоставлен",
  not_found: "Не найден в Naumen",
  mismatch: "Требует выбора",
  check_error: "Ошибка сверки",
  api_unavailable: "Naumen недоступен",
  no_access: "Нет доступа"
};

const wfmLabels: Record<string, string> = {
  working: "Работает",
  dismissed: "Уволен",
  inactive: "Неактивен",
  archived: "Архив",
  unknown: "Не указан"
};

function namesByIds(ids: unknown, dictionary: { id: number; name?: string; title?: string }[]) {
  if (!Array.isArray(ids)) return "";
  return ids.map((id) => dictionary.find((item) => item.id === Number(id))?.name || dictionary.find((item) => item.id === Number(id))?.title || id).join(", ");
}

function oneCLabel(row: AnyRecord) {
  const status = String(row.onec_status || "not_checked");
  return oneCLabels[status] || "Ошибка сверки";
}

function naumenLabel(row: AnyRecord) {
  const status = String(row.naumen_status || "not_linked");
  return naumenLabels[status] || "Ошибка сверки";
}

function wfmLabel(row: AnyRecord) {
  return wfmLabels[String(row.employment_status || "working")] || "Не указан";
}

export function Employees() {
  const [rows, setRows] = useState<AnyRecord[]>([]);
  const [teams, setTeams] = useState<AnyRecord[]>([]);
  const [skills, setSkills] = useState<AnyRecord[]>([]);
  const [contours, setContours] = useState<Contour[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editMode, setEditMode] = useState<"none" | "create" | "edit">("none");
  const [dirty, setDirty] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [menuId, setMenuId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"active" | "archive">("active");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function load(mode = viewMode) {
    const suffix = mode === "archive" ? "?archived=true" : "";
    const [employeesRows, teamRows, skillRows, contourRows] = await Promise.all([getList(`${endpoints.employees}${suffix}`), getList(endpoints.teams), getList(endpoints.skills), getContours()]);
    setRows(employeesRows);
    setTeams(teamRows);
    setSkills(skillRows);
    setContours(contourRows);
  }

  useEffect(() => {
    load().catch(() => setError("Не удалось загрузить сотрудников"));
  }, [viewMode]);

  function updateForm(patch: Partial<typeof emptyForm>) {
    setForm((current) => ({ ...current, ...patch }));
    setDirty(true);
  }

  function closeEditor() {
    if (dirty && !window.confirm("Есть несохранённые изменения. Выйти без сохранения?")) return;
    setEditMode("none");
    setEditingId(null);
    setForm(emptyForm);
    setDirty(false);
  }

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setDirty(false);
    setEditMode("create");
  }

  function openEdit(row: AnyRecord) {
    setEditingId(Number(row.id));
    setForm({
      full_name: String(row.full_name || ""),
      inn: String(row.inn || ""),
      birth_date: String(row.birth_date || ""),
      email: String(row.email || ""),
      phone: String(row.phone || ""),
      position: String(row.position || ""),
      team_id: row.team_id ? String(row.team_id) : "",
      skill_ids: Array.isArray(row.skill_ids) ? row.skill_ids.map(Number) : [],
      project_ids: Array.isArray(row.project_ids) ? row.project_ids.map(Number) : [],
      naumen_uuid: String(row.naumen_uuid || ""),
      employment_type: String(row.employment_type || "full_time"),
      timezone: String(row.timezone || "Europe/Moscow"),
      employment_status: String(row.employment_status || "working"),
      comment: String(row.comment || ""),
      is_active: Boolean(row.is_active ?? true)
    });
    setDirty(false);
    setEditMode("edit");
  }

  async function saveEmployee() {
    setError(null);
    setMessage(null);
    try {
      const { skill_ids, team_id, ...rest } = form;
      const payload = { ...rest, personnel_number: null, team_id: team_id ? Number(team_id) : null, source_type: "manual" };
      let saved: AnyRecord;
      if (editingId) {
        saved = await apiPut(`${endpoints.employees}/${editingId}`, payload);
        await updateEmployeeSkills(editingId, skill_ids);
        setMessage("Сотрудник сохранён.");
      } else {
        saved = await apiPost(endpoints.employees, payload);
        await updateEmployeeSkills(Number(saved.id), skill_ids);
        setMessage("Сотрудник создан.");
      }
      setEditMode("none");
      setEditingId(null);
      setForm(emptyForm);
      setDirty(false);
      await load();
    } catch {
      setError("Не удалось сохранить сотрудника. Проверьте ФИО, ИНН и отсутствие дубля.");
    }
  }

  async function upload(file: File) {
    setError(null);
    setMessage(null);
    try {
      const result = await uploadEmployeeRegistry(file);
      setMessage(`Импорт завершён: создано ${result.rows_created || 0}, обновлено ${result.rows_updated || 0}, ошибок ${result.rows_failed || 0}.`);
      await load();
    } catch {
      setError("Не удалось загрузить реестр сотрудников.");
    }
  }

  async function checkOne(row: AnyRecord) {
    setError(null);
    setMessage(null);
    try {
      const result = await checkEmployeeOneC(Number(row.id));
      const employee = result.employee as AnyRecord | undefined;
      setMessage(`Результат 1С: ${employee ? oneCLabel(employee) : "сверка выполнена"}`);
      await load();
    } catch {
      setError("Сверка с 1С не выполнена. Проверьте ИНН и настройки 1С.");
    }
  }

  async function checkAll() {
    if (!window.confirm("Будет выполнена сверка всех сотрудников с заполненным ИНН. Продолжить?")) return;
    setError(null);
    setMessage(null);
    try {
      const result = await checkAllEmployeesOneC(true);
      setMessage(`Массовая сверка: проверено ${result.employees_checked || 0}, ошибок ${result.employees_failed || 0}.`);
      await load();
    } catch {
      setError("Массовая сверка не запущена. Проверьте настройки 1С.");
    }
  }

  async function checkNaumen(row: AnyRecord) {
    setError(null);
    setMessage(null);
    try {
      const result = await checkEmployeeNaumen(Number(row.id));
      setMessage(`Результат Naumen: ${result.message || naumenLabels[String(result.status)] || "сверка выполнена"}`);
      await load();
    } catch {
      setError("Сверка с Naumen не выполнена. Проверьте ФИО, проект Naumen и загрузку операторов проекта.");
    }
  }

  async function checkNaumenUuid(row: AnyRecord) {
    setError(null);
    setMessage(null);
    try {
      const result = await checkEmployeeNaumenUuid(Number(row.id));
      setMessage(`Проверка UUID Naumen: ${result.message || naumenLabels[String(result.status)] || "проверка выполнена"}`);
      await load();
    } catch {
      setError("Проверка UUID Naumen не выполнена.");
    }
  }

  async function checkAllNaumen() {
    setError(null);
    setMessage(null);
    try {
      const result = await checkAllEmployeesNaumen();
      setMessage(`Naumen: проверено ${result.checked || 0}, сопоставлено ${result.linked || 0}, ошибок ${result.failed || 0}.`);
      await load();
    } catch {
      setError("Массовая сверка с Naumen не выполнена.");
    }
  }

  async function employeeAction(row: AnyRecord, action: "dismiss" | "restore" | "archive") {
    setError(null);
    setMessage(null);
    try {
      await apiPost(`${endpoints.employees}/${row.id}/${action}`, {});
      setMessage(action === "dismiss" ? "Сотрудник уволен в WFM." : action === "restore" ? "Сотрудник восстановлен." : "Сотрудник перенесён в архив.");
      await load();
    } catch {
      setError("Действие по сотруднику не выполнено.");
    }
  }

  async function hardDelete(row: AnyRecord) {
    if (!window.confirm("Окончательно удалить сотрудника только из WFM? 1С и Naumen не изменяются.")) return;
    setError(null);
    setMessage(null);
    try {
      await apiDelete(`${endpoints.employees}/${row.id}/hard-delete`);
      setMessage("Сотрудник окончательно удалён из WFM.");
      await load("archive");
    } catch {
      setError("Окончательное удаление недоступно: у сотрудника есть связанные графики или история. Оставьте запись в архиве.");
    }
  }

  function toggleProject(projectId: number) {
    updateForm({
      project_ids: form.project_ids.includes(projectId)
        ? form.project_ids.filter((id) => id !== projectId)
        : [...form.project_ids, projectId]
    });
  }

  if (editMode !== "none") {
    return (
      <SectionCard title={editMode === "create" ? "Новый сотрудник" : "Редактирование сотрудника"} description="Карточка сотрудника WFM. 1С сверяется по ИНН, Naumen сопоставляется по ФИО или UUID оператора.">
        {message ? <Alert>{message}</Alert> : null}
        {error ? <Alert type="error">{error}</Alert> : null}
        <ActionToolbar>
          <button className="secondary" type="button" onClick={closeEditor}>← Назад</button>
          <button type="button" onClick={saveEmployee}>Сохранить</button>
          <button className="secondary" type="button" onClick={closeEditor}>Отмена</button>
        </ActionToolbar>
        <div className="form-grid separated">
          <div className="form-field"><label>ФИО</label><input value={form.full_name} onChange={(event) => updateForm({ full_name: event.target.value })} /></div>
          <div className="form-field"><label>ИНН</label><input value={form.inn} onChange={(event) => updateForm({ inn: event.target.value })} maxLength={12} /></div>
          <div className="form-field"><label>Дата рождения</label><input type="date" value={form.birth_date} onChange={(event) => updateForm({ birth_date: event.target.value })} /></div>
          <div className="form-field"><label>Email</label><input value={form.email} onChange={(event) => updateForm({ email: event.target.value })} /></div>
          <div className="form-field"><label>Телефон</label><input value={form.phone} onChange={(event) => updateForm({ phone: event.target.value })} /></div>
          <div className="form-field"><label>Должность</label><input value={form.position} onChange={(event) => updateForm({ position: event.target.value })} /></div>
          <div className="form-field"><label>Команда активного проекта</label><select value={form.team_id} onChange={(event) => updateForm({ team_id: event.target.value })}><option value="">Без команды</option>{teams.map((team) => <option key={String(team.id)} value={String(team.id)}>{String(team.name)}</option>)}</select></div>
          <div className="form-field"><label>Статус WFM</label><select value={form.employment_status} onChange={(event) => updateForm({ employment_status: event.target.value })}><option value="working">Работает</option><option value="dismissed">Уволен</option><option value="inactive">Неактивен</option></select></div>
          <div className="form-field full"><label>Проекты/контуры</label><div className="tag-list vertical">{contours.map((contour) => <label key={contour.id} className="checkbox-field"><input type="checkbox" checked={form.project_ids.includes(contour.id)} onChange={() => toggleProject(contour.id)} />{contour.name}</label>)}</div><small>Сотрудник будет виден во всех выбранных контурах.</small></div>
          <div className="form-field full"><label>Навыки</label><select multiple value={form.skill_ids.map(String)} onChange={(event) => updateForm({ skill_ids: Array.from(event.target.selectedOptions).map((option) => Number(option.value)) })}>{skills.map((skill) => <option key={String(skill.id)} value={String(skill.id)}>{String(skill.name)}</option>)}</select><small>Навыки глобальные и не зависят от проекта.</small></div>
          <div className="form-field"><label>UUID Naumen</label><input value={form.naumen_uuid} onChange={(event) => updateForm({ naumen_uuid: event.target.value })} /></div>
          <div className="form-field"><label>Тип занятости</label><input value={form.employment_type} onChange={(event) => updateForm({ employment_type: event.target.value })} /></div>
          <div className="form-field"><label>Часовой пояс</label><input value={form.timezone} onChange={(event) => updateForm({ timezone: event.target.value })} /></div>
          <div className="form-field full"><label>Комментарий</label><input value={form.comment} onChange={(event) => updateForm({ comment: event.target.value })} /></div>
        </div>
      </SectionCard>
    );
  }

  return (
    <SectionCard title="Сотрудники" description="Создавайте сотрудников вручную или загружайте реестр XLSX. Кадровый статус сверяется с 1С по ИНН, операторское сопоставление Naumen выполняется по ФИО.">
      {message ? <Alert>{message}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}
      <ActionToolbar>
        <button type="button" onClick={openCreate}>Создать сотрудника</button>
        <button className="secondary" type="button" onClick={() => downloadEmployeeTemplate().catch(() => setError("Не удалось скачать шаблон."))}>Шаблон</button>
        <button className="secondary" type="button" onClick={() => fileInput.current?.click()}>Загрузить реестр</button>
        <button className="secondary" type="button" onClick={checkAll}>Сверить всех с 1С</button>
        <button className="secondary" type="button" onClick={checkAllNaumen}>Сверить всех с Naumen</button>
      </ActionToolbar>
      <div className="action-toolbar subtle-tabs">
        <button className={viewMode === "active" ? "" : "secondary"} type="button" onClick={() => setViewMode("active")}>Активные</button>
        <button className={viewMode === "archive" ? "" : "secondary"} type="button" onClick={() => setViewMode("archive")}>Архив</button>
      </div>
      <input ref={fileInput} type="file" accept=".xlsx" hidden onChange={(event) => event.target.files?.[0] ? void upload(event.target.files[0]) : undefined} />

      {rows.length === 0 ? <p className="muted-text">{viewMode === "archive" ? "В архиве сотрудников пока нет." : "Сотрудники пока не созданы. Добавьте сотрудника вручную или загрузите Excel-реестр."}</p> : (
        <div className="data-table-wrap separated">
          <table className="data-table interactive-table">
            <thead><tr><th>ФИО</th><th>ИНН</th><th>Проекты</th><th>Команда</th><th>Должность</th><th>WFM</th><th>1С</th><th>Naumen</th><th>Последняя сверка</th><th>Действия</th></tr></thead>
            <tbody>
              {rows.map((row) => (
                <Fragment key={String(row.id)}>
                  <tr className="clickable-row" onClick={() => setExpandedId(expandedId === Number(row.id) ? null : Number(row.id))}>
                    <td>{String(row.full_name || "")}</td>
                    <td>{String(row.inn || "")}</td>
                    <td>{Array.isArray(row.project_names) ? row.project_names.join(", ") : namesByIds(row.project_ids, contours)}</td>
                    <td>{String(row.team_name || "Без команды")}</td>
                    <td>{String(row.position || "")}</td>
                    <td>{wfmLabel(row)}</td>
                    <td><StatusBadge value={oneCLabel(row)} /></td>
                    <td><StatusBadge value={naumenLabel(row)} /></td>
                    <td>{String(row.onec_last_checked_at || row.naumen_last_checked_at || "")}</td>
                    <td onClick={(event) => event.stopPropagation()}>
                      <button className="secondary icon-button" type="button" onClick={() => setMenuId(menuId === Number(row.id) ? null : Number(row.id))}>...</button>
                      {menuId === Number(row.id) ? (
                        <div className="row-action-menu">
                          <button type="button" onClick={() => openEdit(row)}>Редактировать</button>
                          <button type="button" onClick={() => checkOne(row)}>Сверить с 1С</button>
                          <button type="button" onClick={() => checkNaumen(row)}>Сверить с Naumen</button>
                          {viewMode === "archive" ? <button type="button" onClick={() => employeeAction(row, "restore")}>Восстановить</button> : row.employment_status === "dismissed" ? <button type="button" onClick={() => employeeAction(row, "restore")}>Вернуть в работу</button> : <button type="button" onClick={() => employeeAction(row, "dismiss")}>Уволить в WFM</button>}
                          {viewMode === "archive" ? <button type="button" onClick={() => hardDelete(row)}>Удалить из WFM</button> : <button type="button" onClick={() => employeeAction(row, "archive")}>Архивировать</button>}
                        </div>
                      ) : null}
                    </td>
                  </tr>
                  {expandedId === Number(row.id) ? (
                    <tr key={`${String(row.id)}-details`} className="details-row">
                      <td colSpan={10}>
                        <div className="employee-details-grid">
                          <div><h3>Основное</h3><p>{String(row.full_name || "")}</p><p>{String(row.email || "Email не указан")} · {String(row.phone || "Телефон не указан")}</p><p>{String(row.position || "Должность не указана")}</p><p>Статус WFM: {wfmLabel(row)}</p></div>
                          <div><h3>Проекты и команда</h3><p>{Array.isArray(row.project_names) ? row.project_names.join(", ") : namesByIds(row.project_ids, contours)}</p><p>{String(row.team_name || "Команда не назначена")}</p></div>
                          <div><h3>Навыки</h3><div className="tag-list">{Array.isArray(row.skill_ids) && row.skill_ids.length ? row.skill_ids.map((id) => <span className="tag" key={String(id)}>{namesByIds([id], skills.map((skill) => ({ id: Number(skill.id), name: String(skill.name) })))}</span>) : <span className="muted-text">Навыки не назначены</span>}</div><button className="secondary" type="button" onClick={() => openEdit(row)}>Изменить навыки</button></div>
                          <div><h3>1С</h3><p>Статус 1С: {oneCLabel(row)}</p><p>Последняя сверка: {String(row.onec_last_checked_at || "не выполнялась")}</p><p>{String(row.onec_last_check_message || "Сообщений нет")}</p><button className="secondary" type="button" onClick={() => checkOne(row)}>Сверить с 1С</button></div>
                          <div><h3>Naumen</h3><p>UUID: {String(row.naumen_uuid || "не указан")}</p><p>Статус: {naumenLabel(row)}</p><p>{String(row.naumen_last_check_message || "Сообщений нет")}</p><ActionToolbar><button className="secondary" type="button" onClick={() => checkNaumen(row)}>Сверить по ФИО</button><button className="secondary" type="button" onClick={() => checkNaumenUuid(row)}>Проверить UUID</button></ActionToolbar></div>
                          <div><h3>Статистика</h3><p>Статистика пока не загружена.</p></div>
                          <div><h3>Действия</h3><ActionToolbar><button type="button" onClick={() => openEdit(row)}>Редактировать</button>{viewMode === "archive" ? <button className="secondary" type="button" onClick={() => employeeAction(row, "restore")}>Восстановить</button> : <button className="secondary" type="button" onClick={() => employeeAction(row, "archive")}>Архивировать</button>}</ActionToolbar></div>
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </SectionCard>
  );
}
