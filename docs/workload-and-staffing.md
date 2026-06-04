# Нагрузка и потребность

## Нагрузка

Нагрузка — интервальная статистика по очередям: сколько обращений поступило или ожидается, сколько обработано, сколько потеряно, средний AHT и service level.

Загрузка выполняется вручную на странице «Нагрузка»:

- шаблон XLSX: `GET /api/v1/workload/template.xlsx`;
- импорт XLSX: `POST /api/v1/workload/import/xlsx`;
- импорт CSV: `POST /api/v1/workload/import/csv`;
- просмотр: `GET /api/v1/workload`;
- очистка периода: `POST /api/v1/workload/clear-period`.

Шаблон содержит лист «Нагрузка» с колонками: Дата, Начало интервала, Конец интервала, Очередь, Поступило, Обработано, Потеряно, AHT сек, SL %, Тип данных.

## Потребность

Потребность — количество операторов, которое нужно запланировать, чтобы обработать нагрузку.

MVP-формула:

```text
workload_seconds = offered_contacts * average_handle_time_sec
raw_agents = workload_seconds / interval_seconds
base_required = ceil(raw_agents / target_occupancy)
required_with_shrinkage = ceil(base_required / (1 - shrinkage_percent / 100))
```

Если обращений нет, потребность равна 0. Если обращения есть, применяется минимум `min_agents_per_queue`.

Настройки по умолчанию:

- `target_occupancy = 0.85`;
- `shrinkage_percent = 25`;
- `min_agents_per_queue = 1`;
- `calculation_method = mvp`.

Точный Erlang C оставлен на следующий этап.

## Naumen

Naumen может стать источником интервальной нагрузки, AHT и SLA после подтверждения endpoint-а статистики. Пока endpoint не уточнён, UI должен показывать disabled-состояние и не создавать fake-данные.
# Обновление этапа 9.8

Нагрузка — интервальная статистика контакт-центра по очередям: поступило, обработано, потеряно, AHT, SL/SLA. Потребность — расчёт количества операторов по интервалам на основании нагрузки, AHT, целевой занятости и резерва. Автоматическая загрузка из Naumen не создаёт fake-данные и должна включаться только после подтверждения endpoint документацией.
