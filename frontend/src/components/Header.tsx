import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import type { AuthUser } from "../api/client";

export function Header({ title, user, onLogout }: { title: string; user: AuthUser; onLogout: () => void }) {
  const [theme, setTheme] = useState(() => localStorage.getItem("wfm-theme") || "light");

  useEffect(() => {
    document.body.dataset.theme = theme === "dark" ? "dark" : "light";
    localStorage.setItem("wfm-theme", theme);
  }, [theme]);

  return (
    <header className="topbar">
      <div>
        <span>Телесейлз Сервис</span>
        <h1>{title}</h1>
      </div>
      <div className="user-block">
        <span className="env-pill">Внутренняя система</span>
        <strong>{user.full_name}</strong>
        <span>{user.role}</span>
        <button type="button" className="secondary icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} title={theme === "dark" ? "Включить светлую тему" : "Включить тёмную тему"}>
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <button type="button" className="secondary" onClick={onLogout}>Выйти</button>
      </div>
    </header>
  );
}
