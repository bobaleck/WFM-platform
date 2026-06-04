import { endpoints } from "../api/wfm";
import { GenericTablePage } from "./GenericTablePage";

export function Shifts() {
  return <GenericTablePage title="Смены" description="Шаблоны рабочих смен." endpoint={endpoints.shifts} createLabel="Создать смену" emptyText="Создайте шаблоны смен вручную или добавьте типовые смены." fields={[
    { key: "name", label: "Название" },
    { key: "start_time", label: "Начало", type: "time" },
    { key: "end_time", label: "Окончание", type: "time" },
    { key: "break_minutes", label: "Перерыв, минут", type: "number", defaultValue: 60 },
    { key: "paid_hours", label: "Оплачиваемые часы", type: "number", defaultValue: 8 },
    { key: "is_active", label: "Активна", defaultValue: true }
  ]} columns={[
    { key: "name", label: "Название" },
    { key: "start_time", label: "Начало" },
    { key: "end_time", label: "Окончание" },
    { key: "break_minutes", label: "Перерыв" },
    { key: "paid_hours", label: "Оплачиваемые часы" },
    { key: "is_active", label: "Статус", render: (row) => row.is_active ? "Активна" : "Отключена" }
  ]} />;
}
