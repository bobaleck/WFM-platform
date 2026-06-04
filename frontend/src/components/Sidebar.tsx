import { BarChart3, BookOpen, CalendarDays, CalendarX, Clock, Gauge, Info, Layers, ListTodo, PlugZap, ScrollText, Settings, ShieldCheck, UserCog, Users, Waves } from "lucide-react";
import { useEffect, useState } from "react";
import { getContours, getCurrentContour, setCurrentContour, type Contour } from "../api/wfm";
import type { PageKey } from "../routes/App";
import { BrandLogo } from "./BrandLogo";

const navItems: Array<{ key: PageKey; label: string; icon: typeof Gauge; permission: string }> = [
  { key: "dashboard", label: "Дашборд", icon: Gauge, permission: "dashboard:view" },
  { key: "employees", label: "Сотрудники", icon: Users, permission: "employees:view" },
  { key: "teams", label: "Команды", icon: Layers, permission: "teams:view" },
  { key: "skills", label: "Навыки", icon: ShieldCheck, permission: "skills:view" },
  { key: "queues", label: "Очереди", icon: ListTodo, permission: "queues:view" },
  { key: "workload", label: "Нагрузка", icon: Waves, permission: "workload:view" },
  { key: "staffing", label: "Потребность", icon: BarChart3, permission: "staffing:view" },
  { key: "shifts", label: "Смены", icon: Clock, permission: "shifts:view" },
  { key: "schedules", label: "Графики", icon: CalendarDays, permission: "schedules:view" },
  { key: "absences", label: "Отсутствия", icon: CalendarX, permission: "absences:view" },
  { key: "reports", label: "Отчёты", icon: BarChart3, permission: "reports:view" },
  { key: "settings", label: "Настройки", icon: Settings, permission: "settings:view" },
  { key: "users", label: "Пользователи", icon: UserCog, permission: "users:view" },
  { key: "audit", label: "Журнал", icon: ScrollText, permission: "audit:view" },
  { key: "integration", label: "Интеграции", icon: PlugZap, permission: "onec:settings:view" },
  { key: "about", label: "О системе", icon: Info, permission: "dashboard:view" },
  { key: "documentation", label: "Документация", icon: BookOpen, permission: "dashboard:view" }
];

export function Sidebar({ activePage, onNavigate, permissions }: { activePage: PageKey; onNavigate: (page: PageKey) => void; permissions: string[] }) {
  const [contours, setContours] = useState<Contour[]>([]);
  const [current, setCurrent] = useState<Contour | null>(null);
  const canManageSettings = permissions.includes("settings:manage");

  useEffect(() => {
    Promise.all([getContours(), getCurrentContour()]).then(([items, currentContext]) => {
      setContours(items.filter((item) => item.is_active));
      setCurrent(currentContext);
    }).catch(() => {
      setContours([]);
      setCurrent(null);
    });
  }, []);

  const currentValue = current ? String(current.id) : "";

  const changeContext = async (value: string) => {
    const next = await setCurrentContour(value ? Number(value) : null);
    setCurrent(next);
    window.dispatchEvent(new Event("wfm-project-changed"));
  };

  return (
    <aside className="sidebar">
      <div className="brand-block">
        <BrandLogo />
      </div>
      <div className="project-selector">
        <label>Активный контур</label>
        {contours.length === 0 ? (
          <>
            <p className="project-empty">Создайте рабочий контур в настройках.</p>
            {canManageSettings ? <button className="sidebar-link" type="button" onClick={() => onNavigate("settings")}>Настроить контур</button> : null}
          </>
        ) : contours.length === 1 ? (
          <>
            <p className="project-empty">{contours[0].name}</p>
            <small>Данные отображаются в рамках выбранного контура.</small>
          </>
        ) : (
          <select value={currentValue} onChange={(event) => changeContext(event.target.value)}>
            <option value="">Контур не выбран</option>
            {contours.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        )}
        {contours.length > 1 ? <small>Данные отображаются в рамках выбранного контура.</small> : null}
      </div>
      <nav>
        {navItems.filter((item) => permissions.includes(item.permission)).map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.key} className={activePage === item.key ? "nav-item is-active" : "nav-item"} type="button" onClick={() => onNavigate(item.key)}>
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
