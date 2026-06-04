from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.wfm import Absence, ActualWorkInterval, Employee, EmployeeSkill, KpiSnapshot, Permission, PlanningSettings, Queue, QueueSkill, Role, RolePermission, ScheduleAssignment, ScheduleRule, Shift, Skill, StaffingRequirement, Team, User, WorkloadInterval


PERMISSIONS = [
    "dashboard:view", "employees:view", "employees:manage", "teams:view", "teams:manage",
    "skills:view", "skills:manage", "queues:view", "queues:manage", "workload:view",
    "workload:import", "staffing:view", "staffing:calculate", "shifts:view", "shifts:manage",
    "schedules:view", "schedules:generate", "schedules:confirm", "schedules:publish",
    "schedules:manage", "absences:view", "absences:manage", "actual:view", "actual:import",
    "actual:manage", "reports:view", "reports:export", "settings:view", "settings:manage",
    "audit:view", "users:view", "users:manage", "employees:import", "employees:sync_1c",
    "onec:settings:view", "onec:settings:manage", "onec:status-check", "onec:status-check-all",
    "employees:sync_naumen", "employees:view_stats", "workload:sync_naumen",
    "naumen:settings:view", "naumen:settings:manage", "naumen:operators:sync",
]


ROLE_PERMISSIONS = {
    "admin": PERMISSIONS,
    "supervisor": ["dashboard:view", "employees:view", "employees:manage", "employees:import", "employees:sync_1c", "employees:sync_naumen", "employees:view_stats", "onec:status-check", "onec:status-check-all", "teams:view", "teams:manage", "skills:view", "skills:manage", "queues:view", "queues:manage", "shifts:view", "shifts:manage", "schedules:view", "schedules:generate", "schedules:confirm", "schedules:manage", "absences:view", "absences:manage", "reports:view", "workload:import", "workload:sync_naumen", "actual:import", "actual:view", "naumen:operators:sync"],
    "analyst": ["dashboard:view", "employees:view", "employees:view_stats", "employees:import", "employees:sync_1c", "employees:sync_naumen", "onec:status-check", "onec:status-check-all", "teams:view", "skills:view", "queues:view", "workload:view", "workload:import", "workload:sync_naumen", "staffing:view", "staffing:calculate", "reports:view", "reports:export", "naumen:settings:view", "naumen:operators:sync"],
    "customer": ["dashboard:view", "schedules:view", "reports:view", "reports:export"],
    "readonly": ["dashboard:view", "employees:view", "teams:view", "skills:view", "queues:view", "workload:view", "staffing:view", "shifts:view", "schedules:view", "absences:view", "reports:view"],
}


def ensure_auth_defaults(db: Session) -> None:
    permissions_by_code: dict[str, Permission] = {}
    for code in PERMISSIONS:
        permission = db.query(Permission).filter(Permission.code == code).first()
        if not permission:
            permission = Permission(code=code, name=code, description=code)
            db.add(permission)
            db.flush()
        permissions_by_code[code] = permission

    role_names = {
        "admin": "Администратор",
        "supervisor": "Супервизор",
        "analyst": "Аналитик",
        "customer": "Заказчик",
        "readonly": "Только просмотр",
    }
    roles_by_code: dict[str, Role] = {}
    for code, name in role_names.items():
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            role = Role(code=code, name=name, description=name, is_system=True)
            db.add(role)
            db.flush()
        roles_by_code[code] = role

    for role_code, permission_codes in ROLE_PERMISSIONS.items():
        role = roles_by_code[role_code]
        existing = {row.permission_id for row in db.query(RolePermission).filter(RolePermission.role_id == role.id).all()}
        for code in permission_codes:
            permission = permissions_by_code[code]
            if permission.id not in existing:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    admin_role = roles_by_code["admin"]
    admin = db.query(User).filter((User.username == settings.admin_username) | (User.email == settings.admin_email)).first()
    if not admin:
        admin = User(
            email=settings.admin_email,
            username=settings.admin_username,
            full_name=settings.admin_full_name,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            role_id=admin_role.id,
            is_superuser=True,
            is_active=True,
        )
        db.add(admin)
    else:
        admin.role = "admin"
        admin.role_id = admin_role.id
        admin.is_superuser = True
        if not admin.password_hash:
            admin.password_hash = hash_password(settings.admin_password)
    db.commit()


def ensure_stage3_defaults(db: Session) -> None:
    ensure_auth_defaults(db)
    settings_row = db.query(PlanningSettings).order_by(PlanningSettings.id).first()
    if not settings_row:
        db.add(PlanningSettings(
            target_occupancy=0.85,
            default_interval_minutes=30,
            min_agents_per_queue=1,
            max_hours_per_employee_per_week=40,
            min_rest_hours_between_shifts=12,
            max_consecutive_work_days=5,
            preferred_shift_balance_enabled=True,
            weekend_balance_enabled=True,
            skill_priority_weight=50,
            fairness_weight=30,
            coverage_weight=100,
            shrinkage_percent=25,
            service_level_target=80,
            average_patience_sec=20,
            calculation_method="mvp",
        ))
    else:
        settings_row.max_consecutive_work_days = settings_row.max_consecutive_work_days or 5
        settings_row.skill_priority_weight = settings_row.skill_priority_weight or 50
        settings_row.fairness_weight = settings_row.fairness_weight or 30
        settings_row.coverage_weight = settings_row.coverage_weight or 100

    defaults = [
        ("max_weekly_hours", "40", "Максимум часов на сотрудника в неделю"),
        ("min_rest_hours", "12", "Минимальный отдых между сменами"),
        ("allow_overtime", "false", "Разрешать сверхурочные назначения"),
        ("balance_weekend_shifts", "true", "Балансировать выходные смены"),
        ("prefer_skill_match", "true", "Предпочитать совпадение навыков"),
    ]
    existing = {rule.name for rule in db.query(ScheduleRule).all()}
    for name, value, description in defaults:
        if name not in existing:
            db.add(ScheduleRule(name=name, value=value, description=description))
    db.commit()


def ensure_stage4_defaults(db: Session) -> None:
    skill_by_name = {skill.name: skill for skill in db.query(Skill).all()}
    queue_by_name = {queue.name: queue for queue in db.query(Queue).all()}
    queue_skill_pairs = [
        ("Входящая линия", "Входящие звонки"),
        ("Исходящая линия", "Исходящие звонки"),
        ("Чат-поддержка", "Чаты"),
    ]
    for queue_name, skill_name in queue_skill_pairs:
        queue = queue_by_name.get(queue_name)
        skill = skill_by_name.get(skill_name)
        if queue and skill and not db.query(QueueSkill).filter(QueueSkill.queue_id == queue.id, QueueSkill.skill_id == skill.id).first():
            db.add(QueueSkill(queue_id=queue.id, skill_id=skill.id, min_level=2, is_required=True))

    skills = list(skill_by_name.values())
    employees = db.query(Employee).order_by(Employee.id).all()
    if skills and employees:
        for idx, employee in enumerate(employees):
            current = {row.skill_id for row in db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()}
            for offset in (0, 1):
                skill = skills[(idx + offset) % len(skills)]
                if skill.id not in current:
                    db.add(EmployeeSkill(employee_id=employee.id, skill_id=skill.id, level=((idx + offset) % 5) + 1))

    if db.query(ActualWorkInterval).count() == 0:
        published_or_planned = db.query(ScheduleAssignment).filter(ScheduleAssignment.status.in_(["published", "planned"])).limit(6).all()
        for assignment in published_or_planned:
            shift = db.get(Shift, assignment.shift_id)
            if not shift:
                continue
            start = datetime.combine(assignment.work_date, shift.start_time)
            end = start + timedelta(minutes=30)
            db.add(ActualWorkInterval(
                work_date=assignment.work_date,
                employee_id=assignment.employee_id,
                queue_id=assignment.queue_id,
                interval_start=start,
                interval_end=end,
                status="worked",
                actual_minutes=30,
                source="demo",
            ))
    db.commit()


def ensure_stage7_contact_center_demo(db: Session) -> None:
    team_specs = [
        ("Группа 1 — Входящие", "Входящая линия контакт-центра", "Анна Соколова"),
        ("Группа 2 — Исходящие", "Исходящие кампании и продажи", "Игорь Морозов"),
        ("Группа 3 — Чаты", "Текстовые обращения", "Мария Ким"),
        ("Группа контроля качества", "Контроль качества коммуникаций", "Олег Лебедев"),
    ]
    for name, description, supervisor in team_specs:
        if not db.query(Team).filter(Team.name == name).first():
            db.add(Team(name=name, description=description, supervisor_name=supervisor))
    db.flush()

    skill_specs = [
        ("Входящие звонки", "Обработка входящих обращений"),
        ("Исходящие звонки", "Плановые исходящие кампании"),
        ("Чаты", "Текстовые каналы поддержки"),
        ("Контроль качества", "Оценка коммуникаций"),
        ("VIP-клиенты", "Приоритетная линия"),
    ]
    for name, description in skill_specs:
        if not db.query(Skill).filter(Skill.name == name).first():
            db.add(Skill(name=name, description=description))
    db.flush()

    queue_specs = [
        ("Входящая линия", "voice", "Основная входящая линия", 80, 20),
        ("Исходящая линия", "voice", "Исходящие кампании", 75, 30),
        ("Чат-поддержка", "chat", "Онлайн-чаты", 85, 45),
        ("Контроль качества", "backoffice", "Проверка качества обращений", 90, 60),
        ("VIP-линия", "voice", "Приоритетная линия", 90, 15),
    ]
    for name, channel, description, sl, answer_time in queue_specs:
        if not db.query(Queue).filter(Queue.name == name).first():
            db.add(Queue(name=name, channel=channel, description=description, service_level_target=sl, target_answer_time_sec=answer_time))
    db.flush()

    shift_specs = [
        ("4 часа утро", time(8, 0), time(12, 0), 0, 4),
        ("4 часа вечер", time(17, 0), time(21, 0), 0, 4),
        ("6 часов день", time(10, 0), time(16, 0), 30, 6),
        ("8 часов стандарт", time(9, 0), time(18, 0), 60, 8),
        ("12 часов длинная", time(9, 0), time(21, 0), 60, 12),
    ]
    for name, start_time, end_time, break_minutes, paid_hours in shift_specs:
        if not db.query(Shift).filter(Shift.name == name).first():
            db.add(Shift(name=name, start_time=start_time, end_time=end_time, break_minutes=break_minutes, paid_hours=paid_hours))
    db.flush()

    skills = {skill.name: skill for skill in db.query(Skill).all()}
    queues = {queue.name: queue for queue in db.query(Queue).all()}
    queue_skill_specs = [
        ("Входящая линия", "Входящие звонки", 2),
        ("Исходящая линия", "Исходящие звонки", 2),
        ("Чат-поддержка", "Чаты", 2),
        ("Контроль качества", "Контроль качества", 2),
        ("VIP-линия", "VIP-клиенты", 3),
    ]
    for queue_name, skill_name, level in queue_skill_specs:
        queue = queues.get(queue_name)
        skill = skills.get(skill_name)
        if queue and skill and not db.query(QueueSkill).filter(QueueSkill.queue_id == queue.id, QueueSkill.skill_id == skill.id).first():
            db.add(QueueSkill(queue_id=queue.id, skill_id=skill.id, min_level=level, is_required=True))
    db.flush()

    if db.query(Employee).count() == 0:
        teams = {team.name: team for team in db.query(Team).all()}
        employee_specs = [
            ("TS-001", "Елена Васильева", "Оператор", "Группа 1 — Входящие"),
            ("TS-002", "Павел Орлов", "Старший оператор", "Группа 1 — Входящие"),
            ("TS-003", "Дарья Никитина", "Оператор", "Группа 2 — Исходящие"),
            ("TS-004", "Максим Егоров", "Оператор", "Группа 3 — Чаты"),
            ("TS-005", "Софья Белова", "Оператор", "Группа контроля качества"),
            ("TS-006", "Кирилл Волков", "Оператор VIP", "Группа 1 — Входящие"),
        ]
        for idx, (number, full_name, position, team_name) in enumerate(employee_specs, start=1):
            db.add(Employee(personnel_number=number, full_name=full_name, email=f"operator{idx}@telesales.local", position=position, team_id=teams[team_name].id))
        db.flush()

    all_skills = db.query(Skill).order_by(Skill.id).all()
    for idx, employee in enumerate(db.query(Employee).order_by(Employee.id).all()):
        current = {row.skill_id for row in db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == employee.id).all()}
        for offset in (0, 1):
            skill = all_skills[(idx + offset) % len(all_skills)]
            if skill.id not in current:
                db.add(EmployeeSkill(employee_id=employee.id, skill_id=skill.id, level=((idx + offset) % 5) + 1))
    db.flush()

    start_day = date.today() - timedelta(days=date.today().weekday())
    demo_queues = [queues[name] for name in ["Входящая линия", "Исходящая линия", "Чат-поддержка", "Контроль качества", "VIP-линия"] if name in queues]
    for day_offset in range(5):
        work_day = start_day + timedelta(days=day_offset)
        for hour in (8, 9, 10, 11, 13, 14, 15, 17, 18):
            for queue_index, queue in enumerate(demo_queues):
                interval_start = datetime.combine(work_day, time(hour, 0))
                interval_end = interval_start + timedelta(minutes=30)
                if db.query(WorkloadInterval).filter(WorkloadInterval.interval_start == interval_start, WorkloadInterval.queue_id == queue.id).first():
                    continue
                peak = 18 if hour in (9, 10, 14, 15) else 7 if hour in (17, 18) else 12
                offered = peak + queue_index * 5
                handled = max(0, offered - (1 + queue_index % 3))
                abandoned = offered - handled
                aht = 220 + queue_index * 25
                sl = max(60, queue.service_level_target - (6 if hour in (10, 15) else 0) + queue_index)
                db.add(WorkloadInterval(interval_start=interval_start, interval_end=interval_end, queue_id=queue.id, offered_contacts=offered, handled_contacts=handled, abandoned_contacts=abandoned, average_handle_time_sec=aht, service_level_percent=sl))
                required = max(1, round(offered * aht / 1800 / 0.82))
                planned = max(0, required - (1 if hour in (10, 15) else 0))
                db.add(StaffingRequirement(interval_start=interval_start, interval_end=interval_end, queue_id=queue.id, required_agents=required, planned_agents=planned, gap_agents=planned - required, calculation_note="Демо-расчёт Этапа 7"))

    for queue in demo_queues:
        if not db.query(KpiSnapshot).filter(KpiSnapshot.snapshot_date == start_day, KpiSnapshot.queue_id == queue.id).first():
            db.add(KpiSnapshot(snapshot_date=start_day, queue_id=queue.id, service_level_percent=queue.service_level_target - 2, average_speed_answer_sec=queue.target_answer_time_sec, average_handle_time_sec=240, occupancy_percent=76, utilization_percent=82, abandonment_percent=3.5))
    db.commit()


def seed_demo_data(db: Session) -> None:
    ensure_stage3_defaults(db)
    ensure_stage7_contact_center_demo(db)
    if db.query(Employee).count() > 0:
        ensure_stage4_defaults(db)
        return

    teams = [
        Team(name="Продажи", description="Команда исходящих и входящих продаж", supervisor_name="Анна Соколова"),
        Team(name="Поддержка", description="Первая линия клиентской поддержки", supervisor_name="Игорь Морозов"),
        Team(name="Контроль качества", description="Оценка коммуникаций и соблюдения стандартов", supervisor_name="Мария Ким"),
    ]
    db.add_all(teams)
    db.flush()

    skills = [
        Skill(name="Входящие звонки", description="Обработка входящих обращений"),
        Skill(name="Исходящие звонки", description="Плановые исходящие кампании"),
        Skill(name="Чаты", description="Текстовые каналы поддержки"),
        Skill(name="VIP-клиенты", description="Приоритетные клиенты"),
        Skill(name="Продажи", description="Консультационные продажи"),
    ]
    db.add_all(skills)
    db.flush()

    queues = [
        Queue(name="Входящая линия", channel="voice", description="Основная входящая очередь", service_level_target=80, target_answer_time_sec=20),
        Queue(name="Исходящая линия", channel="voice", description="Исходящие продажи", service_level_target=75, target_answer_time_sec=30),
        Queue(name="Чат-поддержка", channel="chat", description="Онлайн-чаты", service_level_target=85, target_answer_time_sec=45),
    ]
    db.add_all(queues)
    db.flush()

    employees = [
        ("TS-001", "Елена Васильева", "Оператор", teams[0]),
        ("TS-002", "Павел Орлов", "Старший оператор", teams[0]),
        ("TS-003", "Дарья Никитина", "Оператор", teams[0]),
        ("TS-004", "Максим Егоров", "Оператор", teams[1]),
        ("TS-005", "Софья Белова", "Оператор", teams[1]),
        ("TS-006", "Кирилл Волков", "Старший оператор", teams[1]),
        ("TS-007", "Алина Федорова", "Специалист контроля качества", teams[2]),
        ("TS-008", "Роман Павлов", "Оператор", teams[1]),
        ("TS-009", "Наталья Зайцева", "Оператор", teams[0]),
        ("TS-010", "Дмитрий Седов", "Оператор", teams[1]),
    ]
    employee_rows: list[Employee] = []
    for idx, (number, name, position, team) in enumerate(employees, start=1):
        row = Employee(
            personnel_number=number,
            full_name=name,
            email=f"operator{idx}@telesales.local",
            phone=f"+7-900-000-{idx:04d}",
            position=position,
            team_id=team.id,
        )
        db.add(row)
        employee_rows.append(row)
    db.flush()

    for idx, employee in enumerate(employee_rows):
        db.add(EmployeeSkill(employee_id=employee.id, skill_id=skills[idx % len(skills)].id, level=(idx % 3) + 1))

    shifts = [
        Shift(name="Утро 09:00-18:00", start_time=time(9, 0), end_time=time(18, 0), break_minutes=60, paid_hours=8),
        Shift(name="День 10:00-19:00", start_time=time(10, 0), end_time=time(19, 0), break_minutes=60, paid_hours=8),
        Shift(name="Вечер 12:00-21:00", start_time=time(12, 0), end_time=time(21, 0), break_minutes=60, paid_hours=8),
    ]
    db.add_all(shifts)
    db.flush()

    start_day = date.today() - timedelta(days=date.today().weekday())
    for day_offset in range(5):
        work_day = start_day + timedelta(days=day_offset)
        for hour in (9, 10, 11, 12, 14, 15, 16):
            for queue_index, queue in enumerate(queues):
                start = datetime.combine(work_day, time(hour, 0))
                end = start + timedelta(minutes=30)
                offered = 28 + hour + queue_index * 7
                handled = offered - (2 + queue_index)
                abandoned = offered - handled
                aht = 240 + queue_index * 35
                sl = 78 + queue_index * 3 + (hour % 3)
                db.add(WorkloadInterval(
                    interval_start=start,
                    interval_end=end,
                    queue_id=queue.id,
                    offered_contacts=offered,
                    handled_contacts=handled,
                    abandoned_contacts=abandoned,
                    average_handle_time_sec=aht,
                    service_level_percent=sl,
                ))
                required = max(2, round(offered * aht / 1800 / 0.75))
                planned = required - 1 if hour in (10, 11, 15) else required
                db.add(StaffingRequirement(
                    interval_start=start,
                    interval_end=end,
                    queue_id=queue.id,
                    required_agents=required,
                    planned_agents=planned,
                    gap_agents=planned - required,
                    calculation_note="Демо-расчёт для MVP",
                ))

    for idx, employee in enumerate(employee_rows):
        db.add(ScheduleAssignment(
            work_date=start_day + timedelta(days=idx % 5),
            employee_id=employee.id,
            shift_id=shifts[idx % len(shifts)].id,
            queue_id=queues[idx % len(queues)].id,
            status="planned",
            note="Демо-график",
        ))

    db.add(Absence(
        employee_id=employee_rows[0].id,
        absence_type="Отпуск",
        date_from=start_day + timedelta(days=3),
        date_to=start_day + timedelta(days=4),
        status="planned",
        comment="Демо-отсутствие",
    ))

    db.add_all([
        KpiSnapshot(snapshot_date=start_day, queue_id=queues[0].id, service_level_percent=82, average_speed_answer_sec=18, average_handle_time_sec=248, occupancy_percent=74, utilization_percent=81, abandonment_percent=3.8),
        KpiSnapshot(snapshot_date=start_day, queue_id=queues[1].id, service_level_percent=76, average_speed_answer_sec=27, average_handle_time_sec=282, occupancy_percent=71, utilization_percent=79, abandonment_percent=5.2),
        KpiSnapshot(snapshot_date=start_day, queue_id=queues[2].id, service_level_percent=87, average_speed_answer_sec=34, average_handle_time_sec=210, occupancy_percent=69, utilization_percent=76, abandonment_percent=2.4),
    ])

    db.commit()
    ensure_stage4_defaults(db)
