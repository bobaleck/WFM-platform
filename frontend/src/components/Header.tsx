import type { AuthUser } from "../api/client";

export function Header({ title, user, onLogout }: { title: string; user: AuthUser; onLogout: () => void }) {
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
        <button type="button" className="secondary" onClick={onLogout}>Выйти</button>
      </div>
    </header>
  );
}
