import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: string; description: string; actions?: ReactNode }) {
  return (
    <div className="section-title">
      <div>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      {actions ? <div className="actions">{actions}</div> : null}
    </div>
  );
}
