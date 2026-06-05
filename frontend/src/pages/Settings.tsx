import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut } from "../api/client";
import { endpoints, getContours, getList, syncContourNaumen, type AnyRecord, type Contour } from "../api/wfm";
import { getNaumenNccCustomers, getNaumenNccProjects, getNaumenNccStatus } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
import { AsyncButton } from "../components/AsyncButton";
import { DataTable } from "../components/DataTable";
import { SectionCard } from "../components/SectionCard";

const defaultSettings: Record<string, string> = {
  company_name: "Телесейлз Сервис",
  system_name: "WFM-платформа",
  timezone: "Europe/Moscow",
  language: "ru",
  date_format: "DD.MM.YYYY",
  auto_create_teams: "true",
  auto_create_skills: "true",
  max_import_rows: "10000",
  csv_delimiter: ",",
  csv_encoding: "UTF-8 BOM",
  export_include_ids: "false"
};

export function Settings() {
  const [tab, setTab] = useState("general");
  const [settings, setSettings] = useState(defaultSettings);
  const [rules, setRules] = useState<AnyRecord[]>([]);
  const [contours, setContours] = useState<Contour[]>([]);
  const [contourForm, setContourForm] = useState({ name: "", description: "" });
  const [nccStatus, setNccStatus] = useState<AnyRecord | null>(null);
  const [nccCustomers, setNccCustomers] = useState<AnyRecord[]>([]);
  const [nccProjects, setNccProjects] = useState<AnyRecord[]>([]);
  const [editingContourId, setEditingContourId] = useState<number | null>(null);
  const [editContourForm, setEditContourForm] = useState({ name: "", description: "", naumen_partner_uuid: "", naumen_project_uuid: "" });
  const [pendingAction, setPendingAction] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    apiGet<Record<string, string>>("/api/v1/settings/app").then((data) => setSettings({ ...defaultSettings, ...data })).catch(() => undefined);
    getList(endpoints.scheduleRules).then(setRules).catch(() => setRules([]));
    getContours().then(setContours).catch(() => setContours([]));
    getNaumenNccStatus().then(setNccStatus).catch(() => setNccStatus({ configured: false, message: "Интеграция Naumen/NCC не настроена" }));
  };

  useEffect(load, []);

  const saveSettings = async () => {
    setError("");
    try {
      setSettings(await apiPut<Record<string, string>>("/api/v1/settings/app", settings));
      setMessage("Настройки сохранены.");
    } catch {
      setError("Не удалось сохранить настройки.");
    }
  };

  const updateRuleValue = async (row: AnyRecord, value: string) => {
    await apiPut(`/api/v1/schedule-rules/${row.id}`, { ...row, value });
    setMessage("Правило обновлено.");
    load();
  };

  const createContour = async () => {
    if (!contourForm.name.trim()) {
      setError("Название контура обязательно.");
      return;
    }
    await apiPost("/api/v1/contours", { ...contourForm, is_active: true, is_default: contours.length === 0 });
    setContourForm({ name: "", description: "" });
    setMessage("Контур создан.");
    load();
  };

  const archiveContour = async (row: AnyRecord) => {
    await apiPost(`/api/v1/contours/${row.id}/archive`, {});
    setMessage("Контур архивирован.");
    load();
  };

  const loadNccCustomers = async () => {
    setError("");
    setPendingAction("ncc-customers");
    try {
      const result = await getNaumenNccCustomers();
      setNccCustomers(Array.isArray(result.items) ? result.items as AnyRecord[] : []);
      setMessage("Список партнёров Naumen/NCC загружен.");
    } catch {
      setError("Интеграция Naumen/NCC не настроена или NCC недоступен.");
    } finally {
      setPendingAction("");
    }
  };

  const bindNccCustomer = async (contourId: number, customerUuid: string) => {
    setError("");
    setMessage("");
    setPendingAction(`bind-${contourId}`);
    try {
      await apiPut(`/api/v1/contours/${contourId}`, { naumen_customer_uuid: customerUuid, naumen_partner_uuid: customerUuid, manual_stats_enabled: !customerUuid });
      setMessage(customerUuid ? "UUID Naumen/NCC привязан к контуру." : "Контур переведён в ручной режим статистики.");
      load();
      if (customerUuid) {
        const projects = await getNaumenNccProjects(customerUuid);
        setNccProjects(Array.isArray(projects.items) ? projects.items as AnyRecord[] : []);
      }
    } catch {
      setError("Не удалось сохранить UUID Naumen/NCC для контура.");
    } finally {
      setPendingAction("");
    }
  };

  const openContourEdit = (row: AnyRecord) => {
    setEditingContourId(Number(row.id));
    setEditContourForm({
      name: String(row.name || ""),
      description: String(row.description || ""),
      naumen_partner_uuid: String(row.naumen_customer_uuid || row.naumen_partner_uuid || ""),
      naumen_project_uuid: String(row.naumen_project_uuid || "")
    });
  };

  const saveContourEdit = async (contourId: number) => {
    setError("");
    setMessage("");
    setPendingAction(`save-contour-${contourId}`);
    try {
      const partnerUuid = editContourForm.naumen_partner_uuid.trim();
      await apiPut(`/api/v1/contours/${contourId}`, {
        name: editContourForm.name,
        description: editContourForm.description,
        naumen_partner_uuid: partnerUuid,
        naumen_customer_uuid: partnerUuid,
        naumen_project_uuid: editContourForm.naumen_project_uuid.trim(),
        manual_stats_enabled: !partnerUuid
      });
      setEditingContourId(null);
      setMessage("Контур сохранён.");
      load();
    } catch {
      setError("Не удалось сохранить контур.");
    } finally {
      setPendingAction("");
    }
  };

  const syncContour = async (contourId: number) => {
    setError("");
    setMessage("");
    setPendingAction(`sync-${contourId}`);
    try {
      const end = new Date();
      end.setDate(end.getDate() + 1);
      const begin = new Date(end);
      begin.setDate(begin.getDate() - 7);
      const result = await syncContourNaumen(contourId, begin.toISOString().slice(0, 10), end.toISOString().slice(0, 10));
      setMessage(`Naumen/NCC синхронизирован: ${JSON.stringify(result.rows_by_type || {})}`);
      load();
    } catch {
      setError("Синхронизация Naumen/NCC не выполнена. Проверьте UUID контура и env backend.");
    } finally {
      setPendingAction("");
    }
  };

  return (
    <>
      <ActionToolbar>
        <button className={tab === "general" ? "" : "secondary"} type="button" onClick={() => setTab("general")}>Общие</button>
        <button className={tab === "planning" ? "" : "secondary"} type="button" onClick={() => setTab("planning")}>Планирование</button>
        <button className={tab === "import" ? "" : "secondary"} type="button" onClick={() => setTab("import")}>Импорт</button>
        <button className={tab === "contours" ? "" : "secondary"} type="button" onClick={() => setTab("contours")}>Контуры</button>
        <button className={tab === "export" ? "" : "secondary"} type="button" onClick={() => setTab("export")}>Экспорт</button>
      </ActionToolbar>
      {message ? <Alert>{message}</Alert> : null}
      {error ? <Alert type="error">{error}</Alert> : null}

      {tab === "general" ? (
        <SectionCard title="Общие настройки" description="Базовые параметры интерфейса и организации.">
          <div className="form-grid">
            {["company_name", "system_name", "timezone", "language", "date_format"].map((key) => <div className="form-field" key={key}><label>{key}</label><input value={settings[key]} onChange={(event) => setSettings({ ...settings, [key]: event.target.value })} /></div>)}
          </div>
          <ActionToolbar><button type="button" onClick={saveSettings}>Сохранить</button></ActionToolbar>
        </SectionCard>
      ) : null}

      {tab === "planning" ? (
        <SectionCard title="Планирование" description="Ограничения и веса MVP-алгоритма графиков.">
          <DataTable columns={[
            { key: "name", label: "Правило" },
            { key: "value", label: "Значение", render: (row) => <input className="inline-input" defaultValue={String(row.value)} onBlur={(event) => updateRuleValue(row, event.target.value)} /> },
            { key: "description", label: "Описание" },
            { key: "is_active", label: "Активно", render: (row) => row.is_active ? "да" : "нет" }
          ]} rows={rules} />
        </SectionCard>
      ) : null}

      {tab === "import" ? (
        <SectionCard title="Импорт" description="Правила загрузки XLSX/CSV-реестров.">
          <div className="form-grid">
            {["auto_create_teams", "auto_create_skills", "max_import_rows", "csv_delimiter", "csv_encoding"].map((key) => <div className="form-field" key={key}><label>{key}</label><input value={settings[key]} onChange={(event) => setSettings({ ...settings, [key]: event.target.value })} /></div>)}
          </div>
          <ActionToolbar><button type="button" onClick={saveSettings}>Сохранить</button></ActionToolbar>
        </SectionCard>
      ) : null}

      {tab === "contours" ? (
        <SectionCard title="Рабочие контуры" description="Контур объединяет разделение WFM-данных, Naumen/NCC партнёра и ручной режим статистики.">
          <div className="info-panel">
            {String(nccStatus?.message || "Статус Naumen/NCC не проверен.")}
          </div>
          <ActionToolbar>
            <AsyncButton className="secondary" type="button" onClick={loadNccCustomers} loading={pendingAction === "ncc-customers"} loadingText="Загружаем партнёров...">Загрузить список партнёров из Naumen</AsyncButton>
          </ActionToolbar>
          <div className="form-grid">
            <div className="form-field"><label>Название</label><input value={contourForm.name} onChange={(event) => setContourForm({ ...contourForm, name: event.target.value })} /></div>
            <div className="form-field"><label>Описание</label><input value={contourForm.description} onChange={(event) => setContourForm({ ...contourForm, description: event.target.value })} /></div>
          </div>
          <ActionToolbar><button type="button" onClick={createContour}>Создать контур</button></ActionToolbar>
          <DataTable rows={contours as unknown as AnyRecord[]} columns={[
            { key: "name", label: "Название" },
            { key: "is_active", label: "Статус", render: (row) => row.is_active ? "Активен" : "Архив" },
            { key: "naumen_customer_uuid", label: "Naumen/NCC партнёр", render: (row) => String(row.naumen_customer_uuid || row.naumen_partner_uuid || "Ручной режим") },
            { key: "naumen_project_uuid", label: "Проект", render: (row) => String(row.naumen_project_uuid || "весь partneruuid") },
            { key: "manual_stats_enabled", label: "Режим", render: (row) => row.naumen_customer_uuid || row.naumen_partner_uuid ? "Naumen/NCC" : "Ручная статистика" },
            { key: "actions", label: "Действия", render: (row) => (
              <div className="contour-cell">
                {editingContourId === Number(row.id) ? (
                  <div className="collapsible-panel is-open">
                    <div className="form-grid compact-form">
                      <div className="form-field"><label>Название</label><input value={editContourForm.name} onChange={(event) => setEditContourForm({ ...editContourForm, name: event.target.value })} /></div>
                      <div className="form-field"><label>Описание</label><input value={editContourForm.description} onChange={(event) => setEditContourForm({ ...editContourForm, description: event.target.value })} /></div>
                      <div className="form-field"><label>Партнёр Naumen/NCC</label><select value={editContourForm.naumen_partner_uuid} onChange={(event) => { setEditContourForm({ ...editContourForm, naumen_partner_uuid: event.target.value }); if (event.target.value) getNaumenNccProjects(event.target.value).then((projects) => setNccProjects(Array.isArray(projects.items) ? projects.items as AnyRecord[] : [])).catch(() => setNccProjects([])); }}>
                        <option value="">Ручной режим</option>
                        {nccCustomers.map((customer) => <option key={String(customer.customer_uuid)} value={String(customer.customer_uuid)}>{String(customer.customer_name)} ({String(customer.active_incoming_projects_count || 0)}/{String(customer.active_outcoming_projects_count || 0)})</option>)}
                      </select></div>
                      <div className="form-field"><label>Дочерний проект</label><select value={editContourForm.naumen_project_uuid} onChange={(event) => setEditContourForm({ ...editContourForm, naumen_project_uuid: event.target.value })}>
                        <option value="">Весь партнёр</option>
                        {nccProjects.map((project) => <option key={String(project.project_uuid)} value={String(project.project_uuid)}>{String(project.project_title)}</option>)}
                      </select></div>
                    </div>
                    <ActionToolbar>
                      <AsyncButton type="button" onClick={() => saveContourEdit(Number(row.id))} loading={pendingAction === `save-contour-${row.id}`} loadingText="Сохраняем...">Сохранить</AsyncButton>
                      <button className="secondary" type="button" onClick={() => setEditingContourId(null)}>Отмена</button>
                    </ActionToolbar>
                  </div>
                ) : null}
                <ActionToolbar>
                  <AsyncButton className="secondary" type="button" onClick={() => syncContour(Number(row.id))} loading={pendingAction === `sync-${row.id}`} loadingText="Синхронизируем...">Синхронизировать Naumen</AsyncButton>
                  <button className="secondary" type="button" onClick={() => openContourEdit(row)}>Редактировать</button>
                  <button className="secondary" type="button" onClick={() => apiPut(`/api/v1/contours/${row.id}`, { is_default: true }).then(load)}>Сделать активным</button>
                  <button className="secondary" type="button" onClick={() => archiveContour(row)}>Архивировать</button>
                </ActionToolbar>
              </div>
            ) }
          ]} emptyText="Создайте рабочий контур в настройках." />
        </SectionCard>
      ) : null}

      {tab === "ncc" ? (
        <SectionCard title="Naumen/NCC" description="Статистика Naumen берётся backend из read-only PostgreSQL NCC. Frontend не подключается к NCC напрямую.">
          <div className="info-panel">
            {String(nccStatus?.message || "Статус Naumen/NCC не проверен.")}
          </div>
          <ActionToolbar>
            <AsyncButton className="secondary" type="button" onClick={loadNccCustomers} loading={pendingAction === "ncc-customers"} loadingText="Загружаем партнёров...">Загрузить партнёров из Naumen/NCC</AsyncButton>
          </ActionToolbar>
          <DataTable rows={contours as unknown as AnyRecord[]} columns={[
            { key: "name", label: "Контур" },
            { key: "naumen_customer_uuid", label: "UUID Naumen/NCC", render: (row) => String(row.naumen_customer_uuid || row.naumen_partner_uuid || "Не указан") },
            { key: "manual_stats_enabled", label: "Режим", render: (row) => row.naumen_customer_uuid || row.naumen_partner_uuid ? "Naumen/NCC" : "Ручная загрузка" },
            { key: "actions", label: "Привязка", render: (row) => (
              <ActionToolbar>
                <select className="inline-input" defaultValue={String(row.naumen_customer_uuid || row.naumen_partner_uuid || "")} onChange={(event) => bindNccCustomer(Number(row.id), event.target.value)}>
                  <option value="">Ручной режим</option>
                  {nccCustomers.map((customer) => <option key={String(customer.customer_uuid)} value={String(customer.customer_uuid)}>{String(customer.customer_name)}</option>)}
                </select>
                <AsyncButton className="secondary" type="button" onClick={() => bindNccCustomer(Number(row.id), String(row.naumen_customer_uuid || row.naumen_partner_uuid || ""))} loading={pendingAction === `bind-${row.id}`} loadingText="Сохраняем...">Сохранить</AsyncButton>
              </ActionToolbar>
            ) }
          ]} emptyText="Создайте рабочий контур перед привязкой Naumen/NCC." />
          {nccProjects.length ? (
            <div className="separated">
              <h3>Дочерние активные проекты выбранного партнёра</h3>
              <DataTable rows={nccProjects} columns={[
                { key: "project_type", label: "Тип" },
                { key: "project_title", label: "Проект" },
                { key: "project_uuid", label: "UUID" },
                { key: "project_state", label: "Статус" }
              ]} />
            </div>
          ) : null}
        </SectionCard>
      ) : null}

      {tab === "export" ? (
        <SectionCard title="Экспорт" description="Параметры выгрузок.">
          <div className="form-grid">
            <div className="form-field"><label>Включать технические ID</label><input value={settings.export_include_ids} onChange={(event) => setSettings({ ...settings, export_include_ids: event.target.value })} /></div>
            <div className="form-field"><label>Часовой пояс выгрузок</label><input value={settings.timezone} onChange={(event) => setSettings({ ...settings, timezone: event.target.value })} /></div>
          </div>
          <ActionToolbar><button type="button" onClick={saveSettings}>Сохранить</button></ActionToolbar>
        </SectionCard>
      ) : null}
    </>
  );
}
