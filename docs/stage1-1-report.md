# Stage 1.1 report: Nginx access and telephony settings stub

Дата выполнения: 2026-05-25.

## 1. Диагностика доступности

Выполненные команды:

```bash
cd /opt/wfm-naumen
docker compose ps
curl -I http://127.0.0.1:5173
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8010/health
ss -tulpn | grep -E ':80|:443|:5173|:8000|:8010' || true
nginx -t
systemctl status nginx --no-pager || true
ls -la /etc/nginx/sites-available /etc/nginx/sites-enabled 2>/dev/null || true
```

Результат:

- Frontend был живой: `HTTP/1.1 200 OK` на `127.0.0.1:5173`.
- Backend был живой: `{"status":"ok","service":"backend"}` на `127.0.0.1:8000`.
- Scheduler был живой: `{"status":"ok","service":"scheduler"}` на `127.0.0.1:8010`.
- Порты `5173`, `8000`, `8010` слушали только `127.0.0.1`.
- Nginx был установлен и активен, но site config для WFM отсутствовал.

Вывод: сайт не открывался из внешнего браузера, потому что frontend был опубликован только на loopback `127.0.0.1:5173`, а reverse proxy на port 80 не был настроен. Решение: системный Nginx на port 80 проксирует WFM UI и API.

## 2. Nginx

Создан project template:

```text
/opt/wfm-naumen/infra/nginx/wfm-naumen.conf
```

Установлен системный конфиг:

```text
/etc/nginx/sites-available/wfm-naumen.conf
/etc/nginx/sites-enabled/wfm-naumen.conf -> /etc/nginx/sites-available/wfm-naumen.conf
```

Конфигурация:

- `listen 80 default_server`;
- `server_name _`;
- `/` -> `http://127.0.0.1:5173`;
- `/api/` -> `http://127.0.0.1:8000/api/`;
- `/health` -> `http://127.0.0.1:8000/health`;
- `/scheduler/` -> `http://127.0.0.1:8010/`;
- `proxy_read_timeout 120s`;
- стандартные proxy headers `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.

`/etc/nginx/sites-enabled/default` не существовал, отключать его не потребовалось.

Проверки:

```text
nginx -t: successful
systemctl reload nginx: выполнен
curl -I http://127.0.0.1/: HTTP/1.1 200 OK
curl -s http://127.0.0.1/health: backend ok
curl -s http://127.0.0.1/api/v1/version: version ok
```

Firewall и системные правила доступа не менялись.

## 3. Backend endpoints

Добавлены endpoints:

```text
GET  /api/v1/integration/settings
POST /api/v1/integration/settings
POST /api/v1/integration/test
GET  /api/v1/integration/status
```

Поведение:

- settings возвращаются без открытого token;
- пустой `api_token` при сохранении не затирает ранее сохранённый token;
- `/test` не выполняет внешний HTTP-запрос;
- если настройки неполные или integration выключена, возвращается `not_configured`;
- если настройки заполнены, возвращается `stub`.

## 4. Хранение token

Создана таблица `integration_settings` через SQLAlchemy auto-create для MVP.

Поля:

- `provider`;
- `display_name`;
- `base_url`;
- `username`;
- `api_token_encrypted`;
- `timeout_seconds`;
- `enabled`;
- `created_at`;
- `updated_at`.

Token хранится не открытым текстом, а как Fernet ciphertext. Ключ берётся из:

```text
INTEGRATION_SECRET_KEY
```

Ключ добавлен в `/opt/wfm-naumen/.env` без вывода значения в консоль. Права `.env` сохранены:

```text
-rw------- /opt/wfm-naumen/.env
```

Проверка БД подтвердила:

```text
fernet_format = true
encrypted_length_ok = true
```

Открытый token в отчёт не записан.

## 5. Frontend

Изменения:

- убраны жёсткие browser-запросы на `http://localhost:8000` и `http://localhost:8010`;
- health теперь используется через относительные пути:
  - `/health`;
  - `/scheduler/health`;
- добавлена страница "Интеграция" / "Настройки телефонии";
- добавлены поля:
  - название интеграции;
  - base URL;
  - username;
  - API token;
  - timeout seconds;
  - enabled;
- добавлены кнопки "Сохранить" и "Проверить подключение";
- token не сохраняется в `localStorage`/`sessionStorage`;
- token не выводится через `console.log`;
- после сохранения UI показывает только masked token.

## 6. Проверки после изменений

Выполнено:

```bash
docker compose up -d --build
docker compose ps
curl -I http://127.0.0.1/
curl -s http://127.0.0.1/health
curl -s http://127.0.0.1/api/v1/version
curl -s http://127.0.0.1/api/v1/integration/status
curl -s http://127.0.0.1/api/v1/integration/settings
curl -s http://127.0.0.1/scheduler/health
```

Результат:

- `wfm-naumen-postgres`: healthy;
- `wfm-naumen-redis`: healthy;
- `wfm-naumen-backend`: healthy;
- `wfm-naumen-scheduler`: healthy;
- `wfm-naumen-frontend`: running;
- `http://127.0.0.1/`: `HTTP/1.1 200 OK`;
- `/health`: backend ok;
- `/scheduler/health`: scheduler ok;
- `/api/v1/integration/status`: возвращает status object;
- `/api/v1/integration/settings`: возвращает settings без открытого token.

Тестовое сохранение использовало только небоевые значения. API вернул masked token, открытый token не возвращался. После проверки режим интеграции возвращён в `enabled=false`, чтобы заглушка не выглядела как активное внешнее подключение.

## 7. URL для открытия сайта

Использовать:

```text
http://<адрес-сервера>/
```

Локальная проверка на сервере:

```text
http://127.0.0.1/
```

## 8. Что не было сделано

- реальные вызовы к внешней телефонии;
- полноценная авторизация пользователей WFM;
- production TLS;
- Alembic migrations;
- интеграция с реальными Naumen endpoints;
- хранение и ротация секретов через отдельный secret manager.

## 9. Следующий этап

- Добавить Alembic migrations.
- Добавить полноценную модель пользователей и права доступа.
- Подтвердить endpoints и права API внешней телефонии/Naumen.
- Реализовать реальный adapter client.
- Добавить аудит изменения integration settings.
- Включить TLS и production reverse proxy hardening.

## 10. Защищённые компоненты

Не трогались:

- SSH/sshd;
- firewall/security rules;
- `mihomo.service`;
- `/etc/mihomo`;
- `/usr/local/bin/mihomo`;
- `codex`;
- `/root/.codex`.
