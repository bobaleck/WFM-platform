import { BarChart3, BookOpen, CalendarDays, CalendarX, ChevronDown, Clock, Gauge, Info, Layers, ListTodo, PlugZap, ScrollText, Settings, ShieldCheck, UserCog, Users, Waves } from "lucide-react";
import { useEffect, useState } from "react";
import { getContours, getCurrentContour, setCurrentContour, type Contour } from "../api/wfm";
import type { PageKey } from "../routes/App";
import { BrandLogo } from "./BrandLogo";

const topItems: Array<{ key: PageKey; label: string; icon: typeof Gauge; permission: string }> = [
  { key: "dashboard", label: "Сводка", icon: Gauge, permission: "dashboard:view" }
];

const navGroups: Array<{ id: string; label: string; icon: typeof Gauge; items: Array<{ key: PageKey; label: string; icon: typeof Gauge; permission: string }> }> = [
  { id: "team", label: "Команда", icon: Users, items: [
    { key: "employees", label: "Сотрудники", icon: Users, permission: "employees:view" },
    { key: "teams", label: "Команды", icon: Layers, permission: "teams:view" },
    { key: "skills", label: "Навыки", icon: ShieldCheck, permission: "skills:view" }
  ] },
  { id: "analytics", label: "Аналитика", icon: BarChart3, items: [
    { key: "queues", label: "Очереди", icon: ListTodo, permission: "queues:view" },
    { key: "workload", label: "Нагрузка", icon: Waves, permission: "workload:view" },
    { key: "staffing", label: "Потребность", icon: BarChart3, permission: "staffing:view" },
    { key: "operators", label: "Операторы", icon: Users, permission: "employees:view" },
    { key: "operatorWorkload", label: "Операторская нагрузка", icon: Clock, permission: "workload:view" },
    { key: "forecastProfile", label: "Профиль нагрузки", icon: BarChart3, permission: "workload:view" }
  ] },
  { id: "worktime", label: "Рабочее время", icon: CalendarDays, items: [
    { key: "schedules", label: "Графики", icon: CalendarDays, permission: "schedules:view" },
    { key: "absences", label: "Отсутствия", icon: CalendarX, permission: "absences:view" },
    { key: "shifts", label: "Смены", icon: Clock, permission: "shifts:view" }
  ] },
  { id: "system", label: "Система", icon: Settings, items: [
    { key: "reports", label: "Отчёты", icon: BarChart3, permission: "reports:view" },
    { key: "settings", label: "Настройки", icon: Settings, permission: "settings:view" },
    { key: "users", label: "Пользователи", icon: UserCog, permission: "users:view" },
    { key: "audit", label: "Журнал", icon: ScrollText, permission: "audit:view" },
    { key: "integration", label: "Интеграции", icon: PlugZap, permission: "onec:settings:view" },
    { key: "about", label: "О системе", icon: Info, permission: "dashboard:view" },
    { key: "documentation", label: "Документация", icon: BookOpen, permission: "dashboard:view" }
  ] }
];

export function Sidebar({ activePage, onNavigate, permissions }: { activePage: PageKey; onNavigate: (page: PageKey) => void; permissions: string[] }) {
  const [contours, setContours] = useState<Contour[]>([]);
  const [current, setCurrent] = useState<Contour | null>(null);
  const [openGroups, setOpenGroups] = useState<string[]>(() => {
    const saved = localStorage.getItem("wfm-sidebar-groups");
    try {
      return saved ? (JSON.parse(saved) as string[]).filter((item) => item !== "summary") : ["team", "analytics", "worktime", "system"];
    } catch {
      return ["team", "analytics", "worktime", "system"];
    }
  });
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
  const toggleGroup = (id: string) => {
    setOpenGroups((currentGroups) => {
      const next = currentGroups.includes(id) ? currentGroups.filter((item) => item !== id) : [...currentGroups, id];
      localStorage.setItem("wfm-sidebar-groups", JSON.stringify(next));
      return next;
    });
  };

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
        {topItems.filter((item) => permissions.includes(item.permission)).map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.key} className={activePage === item.key ? "nav-item is-active" : "nav-item"} type="button" onClick={() => onNavigate(item.key)}>
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
        {navGroups.map((group) => {
          const visibleItems = group.items.filter((item) => permissions.includes(item.permission));
          if (!visibleItems.length) return null;
          const GroupIcon = group.icon;
          const isOpen = openGroups.includes(group.id) || visibleItems.some((item) => item.key === activePage);
          const groupActive = visibleItems.some((item) => item.key === activePage);
          return (
            <div className={groupActive ? "nav-group is-active" : "nav-group"} key={group.id}>
              <button className="nav-group-toggle" type="button" onClick={() => toggleGroup(group.id)}>
                <GroupIcon size={18} />
                <span>{group.label}</span>
                <ChevronDown className={isOpen ? "nav-chevron is-open" : "nav-chevron"} size={16} />
              </button>
              <div className={isOpen ? "nav-group-items is-open" : "nav-group-items"}>
                {visibleItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <button key={item.key} className={activePage === item.key ? "nav-item is-active" : "nav-item"} type="button" onClick={() => onNavigate(item.key)}>
                      <Icon size={18} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
