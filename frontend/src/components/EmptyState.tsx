export function EmptyState({ text = "Данные пока не загружены. Загрузите данные через интеграцию или CSV-импорт." }: { text?: string }) {
  return <div className="empty-state">{text}</div>;
}
