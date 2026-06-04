# Статистика сотрудника

Статистика сотрудника хранится локально и может приходить из ручного импорта, Naumen или другого подтверждённого источника.

## Таблицы

`employee_daily_stats` — дневные показатели:

- обработанные и поступившие обращения;
- AHT;
- service level;
- occupancy;
- adherence;
- login/productive/not ready time;
- источник и raw_data.

`employee_interval_stats` — интервальная статистика по сотруднику и очереди.

`employee_attendance_facts` — фактические выходы: план/факт времени и статус attendance.

## API

- `GET /api/v1/employees/{id}/stats`;
- `GET /api/v1/employees/{id}/attendance`;
- `GET /api/v1/employees/{id}/schedule`;
- `GET /api/v1/employees/{id}/statistics-summary`.

Если данных нет, API возвращает `empty=true` и сообщение «Статистика Naumen пока не загружена.»

## Источники

- `manual`;
- `naumen`;
- `import`.

Endpoint-ы Naumen для статистики сотрудника и интервальной нагрузки должны быть уточнены на следующем этапе. До подтверждения endpoint-ов fake-данные не создаются.
