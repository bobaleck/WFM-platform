import { useEffect, useState } from "react";
import { apiPost, apiPut } from "../api/client";
import { getContours, getList, type AnyRecord, type Contour } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
import { DataTable } from "../components/DataTable";
import { SectionCard } from "../components/SectionCard";

const emptyForm = {
  full_name: "",
  username: "",
  email: "",
  role_id: "",
  is_active: true,
  password: "",
  password_confirm: "",
  project_ids: [] as number[]
};

export function UsersPage() {
  const [users, setUsers] = useState<AnyRecord[]>([]);
  const [roles, setRoles] = useState<AnyRecord[]>([]);
  const [projects, setProjects] = useState<Contour[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm);

  const load = () => {
    getList("/api/v1/users").then(setUsers).catch(() => setUsers([]));
    getList("/api/v1/roles").then(setRoles).catch(() => setRoles([]));
    getContours().then(setProjects).catch(() => setProjects([]));
  };

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setModalOpen(true);
  };

  const openEdit = (row: AnyRecord) => {
    setEditingId(Number(row.id));
    setForm({
      full_name: String(row.full_name || ""),
      username: String(row.username || ""),
      email: String(row.email || ""),
      role_id: row.role_id ? String(row.role_id) : "",
      is_active: Boolean(row.is_active ?? true),
      password: "",
      password_confirm: "",
      project_ids: Array.isArray(row.project_ids) ? row.project_ids.map(Number) : []
    });
    setModalOpen(true);
  };

  useEffect(load, []);

  const toggleProject = (projectId: number) => {
    setForm((current) => ({
      ...current,
      project_ids: current.project_ids.includes(projectId)
        ? current.project_ids.filter((id) => id !== projectId)
        : [...current.project_ids, projectId]
    }));
  };

  const submit = async () => {
    setError("");
    setMessage("");
    if (!form.username || !form.email || !form.role_id || !form.full_name) {
      setError("Заполните ФИО, username, email и роль.");
      return;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.email)) {
      setError("Email указан некорректно.");
      return;
    }
    if (!editingId && form.password.length < 10) {
      setError("Временный пароль должен быть не короче 10 символов.");
      return;
    }
    if (form.password !== form.password_confirm) {
      setError("Пароли не совпадают.");
      return;
    }
    const role = roles.find((item) => Number(item.id) === Number(form.role_id));
    if (projects.length > 0 && role?.code !== "admin" && form.project_ids.length === 0) {
      setError("Для не-admin пользователя выберите хотя бы один проект.");
      return;
    }
    const payload = {
      email: form.email,
      username: form.username,
      full_name: form.full_name,
      role_id: Number(form.role_id),
      is_active: form.is_active,
      is_superuser: role?.code === "admin",
      password: form.password || null,
      project_ids: role?.code === "admin" ? [] : form.project_ids,
      can_sync_project_ids: []
    };
    if (editingId) {
      await apiPut(`/api/v1/users/${editingId}`, payload);
      setMessage("Пользователь обновлён.");
    } else {
      await apiPost("/api/v1/users", payload);
      setMessage("Пользователь создан.");
    }
    setModalOpen(false);
    setEditingId(null);
    setForm(emptyForm);
    load();
  };

  const resetPassword = async (row: AnyRecord) => {
    const password = window.prompt("Введите новый временный пароль не короче 10 символов");
    if (!password) return;
    if (password.length < 10) {
      setError("Пароль должен быть не короче 10 символов.");
      return;
    }
    await apiPost(`/api/v1/users/${row.id}/reset-password`, { password });
    setMessage("Пароль сброшен.");
  };

  const toggleActive = async (row: AnyRecord) => {
    await apiPost(`/api/v1/users/${row.id}/${row.is_active ? "disable" : "enable"}`, {});
    setMessage(row.is_active ? "Пользователь отключён." : "Пользователь включён.");
    load();
  };

  return (
    <>
      <SectionCard title="Пользователи и роли" description="Управление пользователями, ролями и доступом к рабочим контурам." actions={<button type="button" onClick={openCreate}>Создать пользователя</button>}>
        {message ? <Alert>{message}</Alert> : null}
        {error ? <Alert type="error">{error}</Alert> : null}
        <DataTable columns={[
          { key: "email", label: "Email" },
          { key: "username", label: "Логин" },
          { key: "full_name", label: "ФИО" },
          { key: "role", label: "Роль" },
          { key: "project_ids", label: "Проекты", render: (row) => Array.isArray(row.project_ids) && row.project_ids.length ? String(row.project_ids.length) : "все/нет" },
          { key: "is_active", label: "Активен", render: (row) => row.is_active ? "да" : "нет" },
          { key: "last_login_at", label: "Последний вход" },
          { key: "actions", label: "Действия", render: (row) => <ActionToolbar><button className="secondary" type="button" onClick={() => openEdit(row)}>Редактировать</button><button className="secondary" type="button" onClick={() => resetPassword(row)}>Сбросить пароль</button><button className="secondary" type="button" onClick={() => toggleActive(row)}>{row.is_active ? "Отключить" : "Включить"}</button></ActionToolbar> }
        ]} rows={users} />
      </SectionCard>

      {modalOpen ? (
        <div className="modal-backdrop">
          <div className="modal">
            <div className="section-title">
              <div>
                <h2>{editingId ? "Редактировать пользователя" : "Создать пользователя"}</h2>
                <p>Роль и доступ к рабочим контурам задаются вручную.</p>
              </div>
              <button className="secondary" type="button" onClick={() => setModalOpen(false)}>Закрыть</button>
            </div>
            <div className="form-grid">
              <div className="form-field"><label>ФИО</label><input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} /></div>
              <div className="form-field"><label>Username</label><input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></div>
              <div className="form-field"><label>Email</label><input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></div>
              <div className="form-field">
                <label>Роль</label>
                <select value={form.role_id} onChange={(event) => setForm({ ...form, role_id: event.target.value })}>
                  <option value="">Выберите роль</option>
                  {roles.map((role) => <option key={String(role.id)} value={String(role.id)}>{String(role.name || role.code)}</option>)}
                </select>
              </div>
              <div className="form-field"><label>{editingId ? "Новый пароль, если нужно" : "Временный пароль"}</label><input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} /></div>
              <div className="form-field"><label>Подтверждение</label><input type="password" value={form.password_confirm} onChange={(event) => setForm({ ...form, password_confirm: event.target.value })} /></div>
              <label className="checkbox-field"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} />Активен</label>
            </div>
            <h3>Доступ к рабочим контурам</h3>
            {projects.length === 0 ? <p className="muted-text">Контуры ещё не добавлены.</p> : (
              <div className="tag-list vertical">
                {projects.map((project) => (
                  <label key={project.id} className="checkbox-field">
                    <input type="checkbox" checked={form.project_ids.includes(project.id)} onChange={() => toggleProject(project.id)} />
                    {project.name}
                  </label>
                ))}
              </div>
            )}
            <ActionToolbar>
              <button type="button" onClick={submit}>{editingId ? "Сохранить" : "Создать"}</button>
              <button className="secondary" type="button" onClick={() => setModalOpen(false)}>Отмена</button>
            </ActionToolbar>
          </div>
        </div>
      ) : null}
    </>
  );
}
