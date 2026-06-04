import type { ReactNode } from "react";

export function ActionToolbar({ children }: { children: ReactNode }) {
  return <div className="action-toolbar">{children}</div>;
}
