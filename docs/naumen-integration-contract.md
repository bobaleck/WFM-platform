# Future Naumen integration contract

Для интеграции потребуются:

- очереди и их идентификаторы;
- агенты/операторы и привязка к пользователям WFM;
- звонки и интервальная статистика;
- AHT;
- SLA/SL;
- ASA;
- abandon rate/LCR;
- recordings;
- agent states;
- интервальные показатели по очередям;
- возможная синхронизация расписаний обратно в Naumen, если API позволяет.

Открытые вопросы:

- формат авторизации;
- лимиты API;
- доступность realtime и historical endpoints;
- granularity интервалов;
- правила хранения recordings и персональных данных.

## Текущее состояние adapter settings

На Этапе 1.1 добавлена безопасная заготовка настроек:

- `base_url`;
- `username`;
- encrypted API token;
- `timeout_seconds`;
- `enabled`.

Token хранится только на backend в PostgreSQL в зашифрованном виде. Frontend получает только masked token. Реальная проверка подключения и реальные запросы к Naumen/внешней телефонии не выполняются до подтверждения endpoints, прав доступа и политики хранения данных.
