import { useEffect, useState } from "react";
import { CalendarClock, Database, Info, Server, Workflow } from "lucide-react";
import { apiGet, type AuthUser } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

type VersionInfo = {
  app: string;
  version: string;
  environment: string;
  external_source: string;
  onec_integration: string;
};

type HealthInfo = {
  status: string;
  service: string;
};

const modules = [
  "сотрудники",
  "команды",
  "навыки",
  "очереди",
  "нагрузка",
  "потребность",
  "графики",
  "покрытие",
  "план/факт",
  "отчёты",
  "роли",
  "аудит"
];

const openSourceBase = [
  ["Backend", "FastAPI"],
  ["Frontend", "React/Vite"],
  ["Database", "PostgreSQL"],
  ["Cache", "Redis"],
  ["Reverse proxy", "Nginx"],
  ["Containerization", "Docker Compose"]
];

const customModules = ["расчёт потребности", "генерация графиков", "покрытие", "план/факт", "отчёты"];

export function AboutSystem({ user }: { user: AuthUser }) {
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [backend, setBackend] = useState<HealthInfo | null>(null);
  const [scheduler, setScheduler] = useState<HealthInfo | null>(null);
  const [database, setDatabase] = useState<HealthInfo | null>(null);

  useEffect(() => {
    apiGet<VersionInfo>("/api/v1/version").then(setVersion).catch(() => setVersion(null));
    fetch("/health").then((response) => response.json()).then(setBackend).catch(() => setBackend(null));
    fetch("/scheduler/health").then((response) => response.json()).then(setScheduler).catch(() => setScheduler(null));
    if (user.permissions.includes("settings:view")) {
      apiGet<HealthInfo>("/api/v1/health/db").then(setDatabase).catch(() => setDatabase(null));
    }
  }, [user.permissions]);

  return (
    <>
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>WFM-платформа Телесейлз Сервис</h2>
            <p>Система реализована как кастомный WFM-layer на open-source технологическом стеке.</p>
          </div>
          <Info size={28} />
        </div>
        <div className="info-grid">
          <div>
            <span>Версия приложения</span>
            <strong>{version?.version || "недоступно"}</strong>
          </div>
          <div>
            <span>Режим окружения</span>
            <strong>{version?.environment || "недоступно"}</strong>
          </div>
          <div>
            <span>Backend</span>
            <StatusBadge value={backend?.status || "unknown"} />
          </div>
          <div>
            <span>Scheduler</span>
            <StatusBadge value={scheduler?.status || "unknown"} />
          </div>
          {user.permissions.includes("settings:view") && (
            <div>
              <span>База данных</span>
              <StatusBadge value={database?.status || "unknown"} />
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Модули</h2>
          </div>
          <Workflow size={26} />
        </div>
        <div className="tag-list">
          {modules.map((module) => <span key={module}>{module}</span>)}
        </div>
      </section>

      <section className="dashboard-grid">
        <div className="panel">
          <div className="section-title">
            <div>
              <h2>Open-source основа</h2>
            </div>
            <Server size={24} />
          </div>
          <div className="settings-list">
            <dl>
              {openSourceBase.map(([name, value]) => (
                <div key={name}>
                  <dt>{name}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
        <div className="panel">
          <div className="section-title">
            <div>
              <h2>Кастомные WFM-модули</h2>
            </div>
            <Database size={24} />
          </div>
          <div className="tag-list vertical">
            {customModules.map((module) => <span key={module}>{module}</span>)}
          </div>
        </div>
      </section>
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Планировщик</h2>
            <p>Текущий режим рассчитан на MVP-планирование без подключения тяжёлого оптимизатора.</p>
          </div>
          <CalendarClock size={24} />
        </div>
        <div className="settings-list">
          <dl>
            <div>
              <dt>Текущий режим</dt>
              <dd>MVP scoring algorithm</dd>
            </div>
            <div>
              <dt>Будущий режим</dt>
              <dd>open-source optimizer optional</dd>
            </div>
            <div>
              <dt>Статус</dt>
              <dd>не подключён</dd>
            </div>
          </dl>
        </div>
      </section>
    </>
  );
}
