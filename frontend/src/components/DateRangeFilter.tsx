export function DateRangeFilter({ dateFrom, dateTo, onDateFrom, onDateTo }: {
  dateFrom: string;
  dateTo: string;
  onDateFrom: (value: string) => void;
  onDateTo: (value: string) => void;
}) {
  return (
    <>
      <input type="date" value={dateFrom} onChange={(event) => onDateFrom(event.target.value)} />
      <input type="date" value={dateTo} onChange={(event) => onDateTo(event.target.value)} />
    </>
  );
}
