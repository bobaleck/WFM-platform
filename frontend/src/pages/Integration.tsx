import { useEffect, useState } from "react";
import { Alert } from "../components/Alert";
import { ActionToolbar } from "../components/ActionToolbar";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { checkNaumen, checkOneC, diagnoseNaumen, diagnoseOneC, diagnoseOneCEmployeeLookup, getNaumenSettings, getOneCSettings, saveNaumenSettings, saveOneCSettings, type NaumenSettings, type OneCSettings } from "../api/integration";
import { matchNaumenOperators, syncNaumenOperators } from "../api/wfm";

const emptySettings: OneCSettings = {
  connection_mode: "gateway_http",
  gateway_url: "",
  gateway_token_saved: false,
  infobase_type: "server",
  onec_server: "",
  onec_database: "",
  onec_cluster: "",
  file_base_path: "",
  onec_username: "",
  password_saved: false,
  auth_type: "password",
  request_timeout_seconds: 30,
  enabled: false,
  verify_tls: true,
  auto_disable_dismissed: false,
  check_on_employee_create: false,
  enable_weekly_1c_status_check: true,
  weekly_1c_status_check_day: "SUN",
  weekly_1c_status_check_time: "03:00",
  onec_check_batch_size: 50,
  onec_check_pause_ms: 200,
  configured: false,
  last_check_status: null,
  last_check_message: null,
  last_check_at: null
};

const emptyNaumenSettings: NaumenSettings = {
  base_url: "",
  api_version: "v2",
  auth_mode: "api_key",
  username: "",
  api_key_masked: null,
  basic_password_masked: null,
  request_timeout_seconds: 30,
  verify_ssl: true,
  enabled: false,
  configured: false,
  last_check_status: null,
  last_check_message: null,
  last_check_http_status: null,
  last_check_endpoint: null,
  last_check_at: null
};

export function Integration() {
  const [settings, setSettings] = useState<OneCSettings>(emptySettings);
  const [naumenSettings, setNaumenSettings] = useState<NaumenSettings>(emptyNaumenSettings);
  const [naumenSecret, setNaumenSecret] = useState("");
  const [password, setPassword] = useState("");
  const [gatewayToken, setGatewayToken] = useState("");
  const [diagnoseInn, setDiagnoseInn] = useState("");
  const [lookupResult, setLookupResult] = useState<Record<string, unknown> | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setError(null);
    try {
      const [onec, naumen] = await Promise.all([getOneCSettings(), getNaumenSettings()]);
      setSettings(onec);
      setNaumenSettings(naumen);
    } catch {
      setError("Не удалось загрузить настройки 1С.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function save() {
    setMessage(null);
    setError(null);
    try {
      const saved = await saveOneCSettings({ ...settings, password, gateway_token: gatewayToken });
      setSettings(saved);
      setPassword("");
      setGatewayToken("");
      setMessage("Настройки 1С сохранены. Пароль не возвращается в открытом виде.");
    } catch {
      setError("Не удалось сохранить настройки 1С.");
    }
  }

  async function check() {
    setMessage(null);
    setError(null);
    try {
      const result = await checkOneC();
      setMessage(String(result.message || result.status));
      await load();
    } catch {
      setError("Проверка подключения к 1С не выполнена.");
    }
  }

  async function diagnose() {
    setMessage(null);
    setError(null);
    try {
      const result = await diagnoseOneC();
      setMessage(String(result.message || result.status));
      await load();
    } catch {
      setError("Диагностика подключения к 1С не выполнена.");
    }
  }

  async function diagnoseEmployeeLookup() {
    setMessage(null);
    setError(null);
    setLookupResult(null);
    if (!/^\d{12}$/.test(diagnoseInn.trim())) {
      setError("Для диагностики укажите ИНН физлица: 12 цифр.");
      return;
    }
    try {
      const result = await diagnoseOneCEmployeeLookup(diagnoseInn.trim());
      setLookupResult(result);
      setMessage(String(result.message || result.status));
    } catch {
      setError("Диагностика поиска сотрудника не выполнена.");
    }
  }

  async function saveNaumen() {
    setMessage(null);
    setError(null);
    try {
      const payload = naumenSettings.auth_mode === "api_key" ? { ...naumenSettings, api_key: naumenSecret } : { ...naumenSettings, basic_password: naumenSecret };
      const saved = await saveNaumenSettings(payload);
      setNaumenSettings(saved);
      setNaumenSecret("");
      setMessage("Настройки Naumen сохранены. Секрет не возвращается в открытом виде.");
    } catch {
      setError("Не удалось сохранить настройки Naumen.");
    }
  }

  async function checkNaumenConnection() {
    setMessage(null);
    setError(null);
    try {
      const result = await checkNaumen();
      setMessage(String(result.message || result.status));
      await load();
    } catch {
      setError("Проверка Naumen не выполнена.");
    }
  }

  async function diagnoseNaumenConnection() {
    setMessage(null);
    setError(null);
    try {
      const result = await diagnoseNaumen();
      setMessage(String(result.message || result.status));
    } catch {
      setError("Диагностика Naumen не выполнена.");
    }
  }

  async function loadNaumenOperators() {
    setMessage(null);
    setError(null);
    try {
      const result = await syncNaumenOperators();
      setMessage(`Операторы Naumen: получено ${String(result.rows_received || 0)}, создано ${String(result.rows_created || 0)}, обновлено ${String(result.rows_updated || 0)}.`);
    } catch {
      setError("Загрузка операторов Naumen не выполнена. Проверьте настройки и UUID проекта.");
    }
  }

  async function matchNaumenByName() {
    setMessage(null);
    setError(null);
    try {
      const result = await matchNaumenOperators();
      setMessage(`Сопоставление по ФИО: привязано ${String(result.linked || 0)}, требует проверки ${Array.isArray(result.suggestions) ? result.suggestions.length : 0}.`);
    } catch {
      setError("Сопоставление сотрудников с Naumen не выполнено.");
    }
  }

  if (loading) {
    return <SectionCard title="Интеграции" description="Загрузка настроек 1С">Загрузка...</SectionCard>;
  }

  return (
    <div className="integration-layout single">
        <>
          <SectionCard title="1С — кадровый статус" description="Сверка кадрового статуса сотрудников по ИНН через внутренний Windows Gateway.">
            {error ? <Alert type="error">{error}</Alert> : null}
            {message ? <Alert>{message}</Alert> : null}
            <div className="info-panel">
              База 1С не публикуется в Web. WFM отправляет запрос во внутренний Windows Gateway, установленный на Windows-сервере с платформой 1С. Gateway использует COMConnector и подключается к базе внутри локальной сети.
            </div>
            <div className="result-strip">
              <span>Состояние: <StatusBadge value={settings.last_check_status || "Ожидает проверки"} /></span>
              <span>Последняя проверка: <strong>{settings.last_check_at || "не выполнялась"}</strong></span>
              <span>Настроено: <strong>{settings.configured ? "да" : "нет"}</strong></span>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Режим подключения</label>
                <select value={settings.connection_mode} onChange={(event) => setSettings({ ...settings, connection_mode: event.target.value as "gateway_http" | "direct_com" })}>
                  <option value="gateway_http">Через Windows Gateway</option>
                  <option value="direct_com" disabled>Direct COM на Windows — недоступно на Linux</option>
                </select>
              </div>
            </div>

            <h3 className="form-section-title">Windows Gateway</h3>
            <div className="form-grid">
              <div className="form-field full">
                <label>Внутренний адрес Windows Gateway</label>
                <input value={settings.gateway_url || ""} onChange={(event) => setSettings({ ...settings, gateway_url: event.target.value })} placeholder="http://1c-gateway.local:8088" />
                <small>Это адрес внутреннего Windows-сервиса, который обращается к 1С через COMConnector. Это не Web-ссылка на базу 1С.</small>
              </div>
              <div className="form-field">
                <label>Токен Gateway, если используется</label>
                <input type="password" value={gatewayToken} onChange={(event) => setGatewayToken(event.target.value)} placeholder="Оставьте пустым, чтобы не менять" />
                <small>Сохранён: {settings.gateway_token_saved ? "да" : "нет"}</small>
              </div>
              <label className="checkbox-field"><input type="checkbox" checked={settings.verify_tls} onChange={(event) => setSettings({ ...settings, verify_tls: event.target.checked })} /> Проверять TLS</label>
              <div className="form-field">
                <label>Таймаут запроса, сек.</label>
                <input type="number" min={1} max={300} value={settings.request_timeout_seconds} onChange={(event) => setSettings({ ...settings, request_timeout_seconds: Number(event.target.value) })} />
              </div>
            </div>

            <h3 className="form-section-title">Параметры базы 1С</h3>
            <div className="form-grid">
              <div className="form-field">
                <label>Тип базы</label>
                <select value={settings.infobase_type} onChange={(event) => setSettings({ ...settings, infobase_type: event.target.value as "server" | "file" })}>
                  <option value="server">Серверная база 1С</option>
                  <option value="file">Файловая база 1С</option>
                </select>
              </div>
              <div className="form-field">
                <label>Сервер 1С</label>
                <input value={settings.onec_server || ""} onChange={(event) => setSettings({ ...settings, onec_server: event.target.value })} placeholder="1c-server.local" disabled={settings.infobase_type === "file"} />
              </div>
              <div className="form-field">
                <label>Имя информационной базы</label>
                <input value={settings.onec_database || ""} onChange={(event) => setSettings({ ...settings, onec_database: event.target.value })} placeholder="TSS_MAIN" disabled={settings.infobase_type === "file"} />
              </div>
              <div className="form-field">
                <label>Кластер, если используется</label>
                <input value={settings.onec_cluster || ""} onChange={(event) => setSettings({ ...settings, onec_cluster: event.target.value })} disabled={settings.infobase_type === "file"} />
              </div>
              {settings.infobase_type === "file" ? (
                <div className="form-field full">
                  <label>Путь к файловой базе 1С</label>
                  <input value={settings.file_base_path || ""} onChange={(event) => setSettings({ ...settings, file_base_path: event.target.value })} placeholder="\\\\server\\share\\1c_base" />
                </div>
              ) : null}
              <div className="form-field">
                <label>Пользователь 1С</label>
                <input value={settings.onec_username || ""} onChange={(event) => setSettings({ ...settings, onec_username: event.target.value })} />
              </div>
              <div className="form-field">
                <label>Пароль 1С</label>
                <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Оставьте пустым, чтобы не менять" />
                <small>Сохранён: {settings.password_saved ? "да" : "нет"}</small>
              </div>
            </div>

            <h3 className="form-section-title">Поведение сверки</h3>
            <div className="form-grid">
              <label className="checkbox-field"><input type="checkbox" checked={settings.enabled} onChange={(event) => setSettings({ ...settings, enabled: event.target.checked })} /> Интеграция включена</label>
              <label className="checkbox-field"><input type="checkbox" checked={settings.check_on_employee_create} onChange={(event) => setSettings({ ...settings, check_on_employee_create: event.target.checked })} /> Сверять при создании сотрудника</label>
              <label className="checkbox-field"><input type="checkbox" checked={settings.auto_disable_dismissed} onChange={(event) => setSettings({ ...settings, auto_disable_dismissed: event.target.checked })} /> Автоматически отключать уволенных в WFM</label>
              <label className="checkbox-field"><input type="checkbox" checked={settings.enable_weekly_1c_status_check} onChange={(event) => setSettings({ ...settings, enable_weekly_1c_status_check: event.target.checked })} /> Еженедельная сверка включена</label>
            </div>
            <ActionToolbar>
              <button type="button" onClick={save}>Сохранить настройки</button>
              <button className="secondary" type="button" onClick={check}>Проверить подключение</button>
              <button className="secondary" type="button" onClick={diagnose}>Диагностика</button>
            </ActionToolbar>
            <h3 className="form-section-title">Диагностика поиска сотрудника</h3>
            <div className="form-grid">
              <div className="form-field">
                <label>ИНН для диагностики</label>
                <input value={diagnoseInn} onChange={(event) => setDiagnoseInn(event.target.value.replace(/\D/g, "").slice(0, 12))} placeholder="450104295305" />
              </div>
            </div>
            <ActionToolbar>
              <button className="secondary" type="button" onClick={diagnoseEmployeeLookup}>Диагностика поиска сотрудника</button>
            </ActionToolbar>
            {lookupResult ? (
              <div className="diagnostic-result">
                <p><strong>Статус:</strong> {String(lookupResult.status || "")}</p>
                <p><strong>Версия Gateway:</strong> {String(lookupResult.gateway_version || "не указана")}</p>
                <p><strong>Физлицо:</strong> {lookupResult.found_person ? "найдено" : "не найдено"}</p>
                <p><strong>Карточки сотрудников:</strong> {lookupResult.cards_found ? "найдены" : "не найдены"}</p>
                <p><strong>Стратегия:</strong> {String(lookupResult.lookup_strategy_used || "не определена")}</p>
                <p><strong>Рекомендация:</strong> {String(lookupResult.recommendation || "Если карточки не найдены, обновите gateway.ps1 на Windows Server.")}</p>
                {Array.isArray(lookupResult.query_errors) && lookupResult.query_errors.length ? <p><strong>Ошибки:</strong> {lookupResult.query_errors.map(String).join("; ")}</p> : null}
                {Array.isArray(lookupResult.query_warnings) && lookupResult.query_warnings.length ? <p><strong>Предупреждения:</strong> {lookupResult.query_warnings.map(String).join("; ")}</p> : null}
              </div>
            ) : null}
          </SectionCard>

          <SectionCard title="Naumen — операторы и статистика" description="Naumen используется для UUID операторов, состава проекта и статистики контакт-центра. Не является кадровым источником увольнений.">
            <div className="info-panel">
              Naumen возвращён как отдельная интеграция. WFM не создаёт и не заменяет сотрудников автоматически: операторы Naumen загружаются в локальный список и сопоставляются с WFM-сотрудниками по ФИО внутри проекта. UUID используется как ручной fallback.
            </div>
            <div className="result-strip">
              <span>Состояние: <StatusBadge value={naumenSettings.last_check_status || "Ожидает проверки"} /></span>
              <span>Endpoint: <strong>{naumenSettings.last_check_endpoint || "не проверялся"}</strong></span>
              <span>Настроено: <strong>{naumenSettings.configured ? "да" : "нет"}</strong></span>
            </div>
            <div className="form-grid">
              <div className="form-field full"><label>Base URL Naumen</label><input value={naumenSettings.base_url || ""} onChange={(event) => setNaumenSettings({ ...naumenSettings, base_url: event.target.value })} placeholder="https://naumen.internal" /></div>
              <div className="form-field"><label>API version</label><select value={naumenSettings.api_version} onChange={(event) => setNaumenSettings({ ...naumenSettings, api_version: event.target.value as "v2" | "current" })}><option value="v2">v2</option><option value="current">current</option></select></div>
              <div className="form-field"><label>Auth mode</label><select value={naumenSettings.auth_mode} onChange={(event) => setNaumenSettings({ ...naumenSettings, auth_mode: event.target.value as "api_key" | "basic" })}><option value="api_key">API token</option><option value="basic">Basic</option></select></div>
              <div className="form-field"><label>Пользователь</label><input value={naumenSettings.username || ""} onChange={(event) => setNaumenSettings({ ...naumenSettings, username: event.target.value })} /></div>
              <div className="form-field"><label>{naumenSettings.auth_mode === "api_key" ? "API token" : "Пароль Basic"}</label><input type="password" value={naumenSecret} onChange={(event) => setNaumenSecret(event.target.value)} placeholder="Оставьте пустым, чтобы не менять" /><small>Сохранён: {naumenSettings.api_key_masked || naumenSettings.basic_password_masked ? "да" : "нет"}</small></div>
              <div className="form-field"><label>Таймаут, сек.</label><input type="number" min={1} max={300} value={naumenSettings.request_timeout_seconds} onChange={(event) => setNaumenSettings({ ...naumenSettings, request_timeout_seconds: Number(event.target.value) })} /></div>
              <label className="checkbox-field"><input type="checkbox" checked={naumenSettings.verify_ssl} onChange={(event) => setNaumenSettings({ ...naumenSettings, verify_ssl: event.target.checked })} /> Проверять SSL</label>
              <label className="checkbox-field"><input type="checkbox" checked={naumenSettings.enabled} onChange={(event) => setNaumenSettings({ ...naumenSettings, enabled: event.target.checked })} /> Интеграция включена</label>
            </div>
            <ActionToolbar>
              <button type="button" onClick={saveNaumen}>Сохранить Naumen</button>
              <button className="secondary" type="button" onClick={checkNaumenConnection}>Проверить Naumen</button>
              <button className="secondary" type="button" onClick={diagnoseNaumenConnection}>Диагностика Naumen</button>
              <button className="secondary" type="button" onClick={loadNaumenOperators}>Загрузить операторов проекта</button>
              <button className="secondary" type="button" onClick={matchNaumenByName}>Сопоставить по ФИО</button>
              <button className="secondary" type="button" disabled title="Endpoint очередей проекта Naumen не подтверждён текущей документацией. Очереди создаются вручную.">Загрузить очереди проекта</button>
              <button className="secondary" type="button" disabled title="Endpoint интервальной нагрузки Naumen не подтверждён текущей документацией. Используйте ручную загрузку XLSX/CSV.">Загрузить нагрузку проекта</button>
            </ActionToolbar>
            <p className="muted-text">Для X5 Retail Group используется UUID проекта Naumen: corebo00000000000p2hcq728jesuk0o. Endpoint интервальной статистики Naumen ожидает подтверждения документацией, fake-данные не создаются.</p>
          </SectionCard>

          <SectionCard title="Автоматическая сверка" description="Еженедельная сверка статусов сотрудников по ИНН.">
            <div className="form-grid">
              <label className="checkbox-field"><input type="checkbox" checked={settings.enable_weekly_1c_status_check} onChange={(event) => setSettings({ ...settings, enable_weekly_1c_status_check: event.target.checked })} /> Включить еженедельную сверку</label>
              <div className="form-field">
                <label>День недели</label>
                <select value={settings.weekly_1c_status_check_day} onChange={(event) => setSettings({ ...settings, weekly_1c_status_check_day: event.target.value })}>
                  <option value="MON">Понедельник</option><option value="TUE">Вторник</option><option value="WED">Среда</option><option value="THU">Четверг</option><option value="FRI">Пятница</option><option value="SAT">Суббота</option><option value="SUN">Воскресенье</option>
                </select>
              </div>
              <div className="form-field"><label>Время</label><input value={settings.weekly_1c_status_check_time} onChange={(event) => setSettings({ ...settings, weekly_1c_status_check_time: event.target.value })} /></div>
              <div className="form-field"><label>Размер пачки</label><input type="number" value={settings.onec_check_batch_size} onChange={(event) => setSettings({ ...settings, onec_check_batch_size: Number(event.target.value) })} /></div>
              <div className="form-field"><label>Пауза, мс</label><input type="number" value={settings.onec_check_pause_ms} onChange={(event) => setSettings({ ...settings, onec_check_pause_ms: Number(event.target.value) })} /></div>
            </div>
            <ActionToolbar><button type="button" onClick={save}>Сохранить расписание</button></ActionToolbar>
          </SectionCard>

          <SectionCard title="Как работает сверка" description="Правило кадрового статуса">
            <p className="muted-text">WFM отправляет ИНН сотрудника во внутренний Windows Gateway. Gateway подключается к 1С через COMConnector, находит физлицо по ИНН и проверяет карточки сотрудников. Если найдена хотя бы одна карточка без даты увольнения — сотрудник считается работающим.</p>
            <p className="muted-text">{settings.last_check_message || "Подключение ещё не проверялось."}</p>
          </SectionCard>
        </>
    </div>
  );
}
