export function MetricTrend({ value, label, tone = "neutral" }: { value: string | number; label: string; tone?: "neutral" | "good" | "warning" | "danger" }) {
  return <span className={`metric-trend ${tone}`}>{value} {label}</span>;
}
