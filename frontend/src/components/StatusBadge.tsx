export function StatusBadge({ value }: { value: unknown }) {
  const text = String(value ?? "");
  const normalized = text.toLowerCase().replace(/[^a-zа-я0-9_-]+/gi, "-");
  return <span className={`status-badge status-${normalized}`}>{text}</span>;
}
