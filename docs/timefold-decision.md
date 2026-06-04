# Timefold decision

Дата: 2026-05-26.

## Текущее состояние

Текущий планировщик — MVP scoring algorithm внутри backend. Он выбирает сотрудников по обязательным навыкам, уровню навыков, fairness, отдыху и недельному лимиту часов. Это не промышленный оптимизатор.

## Когда имеет смысл подключать Timefold

Timefold имеет смысл рассматривать после накопления реальных правил, тестовых наборов и понятных hard/soft constraints. До этого подключение Java-optimizer усложнит архитектуру быстрее, чем даст управляемую пользу.

## Данные, которые уже есть

- сотрудники;
- навыки;
- очереди;
- смены;
- отсутствия;
- потребность;
- правила.

## Ограничения для моделирования

- skill matching;
- max weekly hours;
- min rest hours;
- coverage;
- fairness;
- weekend balance;
- shift preferences.

## Будущая архитектура

Scheduler service может стать отдельным optimization service. Backend отдаёт planning problem, optimizer возвращает schedule solution, backend сохраняет draft assignments и рекомендации.

## Решение

На текущем этапе Timefold не устанавливается и Java-зависимости не подключаются. Пока оставить MVP scoring. Вернуться к Timefold после накопления реальных правил, исторических данных и UAT-сценариев.
