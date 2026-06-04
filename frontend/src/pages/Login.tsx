import { useState } from "react";
import { apiPost, setToken, type AuthUser } from "../api/client";

export function Login({ onLogin }: { onLogin: (user: AuthUser) => void }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    try {
      const result = await apiPost<{ access_token: string; user: AuthUser }>("/api/v1/auth/login", { username, password });
      setToken(result.access_token);
      onLogin(result.user);
    } catch {
      setError("Неверный логин или пароль");
    }
  };

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <span>Телесейлз Сервис</span>
        <h1>WFM-платформа</h1>
        <label>Логин или email<input value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>Пароль<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error ? <p className="error-text">{error}</p> : null}
        <button type="submit">Войти</button>
      </form>
    </main>
  );
}
