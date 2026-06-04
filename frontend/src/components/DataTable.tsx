import type { AnyRecord } from "../api/wfm";
import type { ReactNode } from "react";

export type Column = {
  key: string;
  label: string;
  render?: (row: AnyRecord) => ReactNode;
};

type DataTableProps = {
  columns: Column[];
  rows: AnyRecord[];
  emptyText?: string;
};

export function DataTable({ columns, rows, emptyText = "Данные пока не добавлены." }: DataTableProps) {
  const isNumericColumn = (key: string) => /count|total|agents|hours|percent|minutes|seconds|aht|sla|gap|rows|id$|planned|required|actual|handled|offered|abandoned/i.test(key);

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => <th key={column.key}>{column.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={columns.length}>{emptyText}</td></tr>
          ) : rows.map((row) => (
            <tr key={String(row.id ?? JSON.stringify(row))}>
              {columns.map((column) => (
                <td key={column.key} className={isNumericColumn(column.key) ? "is-numeric" : undefined}>{column.render ? column.render(row) : String(row[column.key] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
