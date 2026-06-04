import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { apiGet, clearToken, getToken, type AuthUser } from "../api/client";
import { Layout } from "../components/Layout";
import { Absences } from "../pages/Absences";
import { AboutSystem } from "../pages/AboutSystem";
import { AuditLogPage } from "../pages/AuditLog";
import { Dashboard } from "../pages/Dashboard";
import { Documentation } from "../pages/Documentation";
import { Employees } from "../pages/Employees";
import { Integration } from "../pages/Integration";
import { Login } from "../pages/Login";
import { Queues } from "../pages/Queues";
import { Reports } from "../pages/Reports";
import { Schedules } from "../pages/Schedules";
import { Settings } from "../pages/Settings";
import { Shifts } from "../pages/Shifts";
import { Skills } from "../pages/Skills";
import { Staffing } from "../pages/Staffing";
import { Teams } from "../pages/Teams";
import { UsersPage } from "../pages/Users";
import { Workload } from "../pages/Workload";

export type PageKey = "dashboard" | "employees" | "teams" | "skills" | "queues" | "workload" | "staffing" | "shifts" | "schedules" | "absences" | "reports" | "settings" | "users" | "audit" | "integration" | "about" | "documentation";

const titles: Record<PageKey, string> = {
  dashboard: "Дашборд",
  employees: "Сотрудники",
  teams: "Команды",
  skills: "Навыки",
  queues: "Очереди",
  workload: "Нагрузка",
  staffing: "Потребность",
  shifts: "Смены",
  schedules: "Графики",
  absences: "Отсутствия",
  reports: "Отчёты",
  settings: "Настройки",
  users: "Пользователи и роли",
  audit: "Журнал действий",
  integration: "Интеграции",
  about: "О системе",
  documentation: "Документация"
};

export function App() {
  const [page, setPage] = useState<PageKey>("dashboard");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!checked && getToken()) {
      apiGet<AuthUser>("/api/v1/auth/me").then(setUser).finally(() => setChecked(true));
    } else if (!checked) {
      setChecked(true);
    }
  }, [checked]);

  useEffect(() => {
    const onAuthRequired = () => {
      setUser(null);
      setPage("dashboard");
      window.history.replaceState(null, "", "/login");
    };
    window.addEventListener("wfm-auth-required", onAuthRequired);
    return () => window.removeEventListener("wfm-auth-required", onAuthRequired);
  }, []);

  const content = useMemo(() => {
    const pages: Record<PageKey, ReactNode> = {
      dashboard: <Dashboard />,
      employees: <Employees />,
      teams: <Teams />,
      skills: <Skills />,
      queues: <Queues />,
      workload: <Workload />,
      staffing: <Staffing />,
      shifts: <Shifts />,
      schedules: <Schedules />,
      absences: <Absences />,
      reports: <Reports />,
      settings: <Settings />,
      users: <UsersPage />,
      audit: <AuditLogPage />,
      integration: <Integration />,
      about: user ? <AboutSystem user={user} /> : null,
      documentation: <Documentation />
    };
    return pages[page];
  }, [page, user]);

  if (!checked) {
    return <section className="panel">Проверка сессии...</section>;
  }

  if (!user) {
    if (window.location.pathname !== "/login") {
      window.history.replaceState(null, "", "/login");
    }
    return <Login onLogin={setUser} />;
  }

  const logout = () => {
    clearToken();
    setUser(null);
    setPage("dashboard");
    window.history.replaceState(null, "", "/login");
  };

  if (window.location.pathname === "/login") {
    window.history.replaceState(null, "", "/");
  }

  return (
    <Layout title={titles[page]} activePage={page} onNavigate={setPage} user={user} onLogout={logout}>
      {content}
    </Layout>
  );
}
