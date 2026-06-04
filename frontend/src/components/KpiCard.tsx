type KpiCardProps = {
  label: string;
  value: string | number;
  hint?: string;
};

export function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <section className="kpi-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </section>
  );
}
