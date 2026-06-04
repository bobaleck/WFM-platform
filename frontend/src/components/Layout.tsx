import type { ReactNode } from "react";
import type { AuthUser } from "../api/client";
import type { PageKey } from "../routes/App";
import { AppShell } from "./AppShell";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function Layout({ title, activePage, onNavigate, user, onLogout, children }: { title: string; activePage: PageKey; onNavigate: (page: PageKey) => void; user: AuthUser; onLogout: () => void; children: ReactNode }) {
  return (
    <AppShell>
      <Sidebar activePage={activePage} onNavigate={onNavigate} permissions={user.permissions} />
      <main className="main-content">
        <Header title={title} user={user} onLogout={onLogout} />
        {children}
      </main>
    </AppShell>
  );
}
