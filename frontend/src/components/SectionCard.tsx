import type { ReactNode } from "react";

export function SectionCard({ title, description, actions, children }: { title?: string; description?: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel section-card">
      {(title || description || actions) ? (
        <div className="section-title">
          <div>
            {title ? <h2>{title}</h2> : null}
            {description ? <p>{description}</p> : null}
          </div>
          {actions ? <div className="actions">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}
