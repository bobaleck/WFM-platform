import { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut } from "../api/client";
import { endpoints, getContours, getList, type AnyRecord, type Contour } from "../api/wfm";
import { ActionToolbar } from "../components/ActionToolbar";
import { Alert } from "../components/Alert";
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
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    apiGet<Record<string, string>>("/api/v1/settings/app").then((data) => setSettings({ ...defaultSettings, ...data })).catch(() => undefined);
    getList(endpoints.scheduleRules).then(setRules).catch(() => setRules([]));
    getContours().then(setContours).catch(() => setContours([]));
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
        <SectionCard title="Рабочие контуры" description="Контуры создаются вручную администратором и используются для разделения данных.">
          <div className="form-grid">
            <div className="form-field"><label>Название</label><input value={contourForm.name} onChange={(event) => setContourForm({ ...contourForm, name: event.target.value })} /></div>
            <div className="form-field"><label>Описание</label><input value={contourForm.description} onChange={(event) => setContourForm({ ...contourForm, description: event.target.value })} /></div>
          </div>
          <ActionToolbar><button type="button" onClick={createContour}>Создать контур</button></ActionToolbar>
          <DataTable rows={contours as unknown as AnyRecord[]} columns={[
            { key: "name", label: "Название" },
            { key: "description", label: "Описание" },
            { key: "is_default", label: "По умолчанию", render: (row) => row.is_default ? "да" : "нет" },
            { key: "is_active", label: "Активен", render: (row) => row.is_active ? "да" : "нет" },
            { key: "actions", label: "Действия", render: (row) => <ActionToolbar><button className="secondary" type="button" onClick={() => apiPut(`/api/v1/contours/${row.id}`, { is_default: true }).then(load)}>По умолчанию</button><button className="secondary" type="button" onClick={() => archiveContour(row)}>Архивировать</button></ActionToolbar> }
          ]} emptyText="Создайте рабочий контур в настройках." />
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
