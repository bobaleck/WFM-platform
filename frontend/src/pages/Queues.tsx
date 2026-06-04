import { useEffect, useState } from "react";
import { apiDelete, apiPost, apiPut } from "../api/client";
import { endpoints, getList, type AnyRecord } from "../api/wfm";
import { DataTable } from "../components/DataTable";
import { PageHeader } from "../components/PageHeader";

export function Queues() {
  const [queues, setQueues] = useState<AnyRecord[]>([]);
  const [skills, setSkills] = useState<AnyRecord[]>([]);
  const [queueSkills, setQueueSkills] = useState<AnyRecord[]>([]);
  const [selectedQueue, setSelectedQueue] = useState<AnyRecord | null>(null);
  const [selectedSkillId, setSelectedSkillId] = useState("");
  const [minLevel, setMinLevel] = useState("2");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<AnyRecord | null>(null);
  const [form, setForm] = useState<AnyRecord>({ name: "", channel: "voice", service_level_target: 80, target_answer_time_sec: 20, description: "", is_active: true });

  const loadQueues = () => getList(endpoints.queues).then(setQueues);
  const loadSkills = () => getList(endpoints.skills).then(setSkills);
  const loadQueueSkills = (queueId: unknown) => getList(`/api/v1/queues/${queueId}/skills`).then(setQueueSkills);

  useEffect(() => {
    loadQueues();
    loadSkills();
  }, []);

  const selectQueue = async (queue: AnyRecord) => {
    setSelectedQueue(queue);
    await loadQueueSkills(queue.id);
  };

  const addSkill = async () => {
    if (!selectedQueue || !selectedSkillId) {
      return;
    }
    await apiPost(`/api/v1/queues/${selectedQueue.id}/skills`, {
      skill_id: Number(selectedSkillId),
      min_level: Number(minLevel),
      is_required: true
    });
    setMessage("Требование по навыку сохранено");
    await loadQueueSkills(selectedQueue.id);
  };

  const removeSkill = async (row: AnyRecord) => {
    if (!selectedQueue) {
      return;
    }
    await apiDelete(`/api/v1/queues/${selectedQueue.id}/skills/${row.id}`);
    await loadQueueSkills(selectedQueue.id);
  };

  const openForm = (row?: AnyRecord) => {
    setEditing(row || {});
    setForm({
      name: row?.name || "",
      channel: row?.channel || "voice",
      service_level_target: row?.service_level_target || 80,
      target_answer_time_sec: row?.target_answer_time_sec || 20,
      description: row?.description || "",
      is_active: row?.is_active ?? true
    });
  };

  const saveQueue = async () => {
    setError("");
    try {
      const payload = { ...form, service_level_target: Number(form.service_level_target), target_answer_time_sec: Number(form.target_answer_time_sec) };
      if (editing?.id) {
        await apiPut(`/api/v1/queues/${editing.id}`, payload);
        setMessage("Очередь обновлена.");
      } else {
        await apiPost("/api/v1/queues", payload);
        setMessage("Очередь создана.");
      }
      setEditing(null);
      await loadQueues();
    } catch {
      setError("Не удалось сохранить очередь.");
    }
  };

  const archiveQueue = async (row: AnyRecord) => {
    try {
      await apiPost(`/api/v1/queues/${row.id}/archive`, {});
      setMessage("Очередь архивирована.");
      await loadQueues();
    } catch {
      setError("Не удалось архивировать очередь.");
    }
  };

  return (
    <>
      <section className="panel">
        <PageHeader title="Очереди" description="Каналы и очереди контактного центра с требованиями по навыкам." />
        <p className="muted-text">Очереди создаются вручную. Они нужны для загрузки нагрузки и расчёта потребности.</p>
        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
        <div className="form-row"><button type="button" onClick={() => openForm()}>Создать очередь</button></div>
        {editing ? (
          <div className="form-grid">
            <div className="form-field"><label>Название</label><input value={String(form.name)} onChange={(event) => setForm({ ...form, name: event.target.value })} /></div>
            <div className="form-field"><label>Канал</label><select value={String(form.channel)} onChange={(event) => setForm({ ...form, channel: event.target.value })}><option value="phone_inbound">Входящие звонки</option><option value="phone_outbound">Исходящие звонки</option><option value="chat">Чат</option><option value="email">Email</option><option value="backoffice">Backoffice</option><option value="quality_control">Контроль качества</option><option value="other">Другое</option><option value="voice">Voice</option></select></div>
            <div className="form-field"><label>Целевой SL, %</label><input type="number" value={String(form.service_level_target)} onChange={(event) => setForm({ ...form, service_level_target: event.target.value })} /></div>
            <div className="form-field"><label>Ответ, сек</label><input type="number" value={String(form.target_answer_time_sec)} onChange={(event) => setForm({ ...form, target_answer_time_sec: event.target.value })} /></div>
            <div className="form-field full"><label>Описание</label><input value={String(form.description)} onChange={(event) => setForm({ ...form, description: event.target.value })} /></div>
            <div className="form-row"><button type="button" onClick={saveQueue}>Сохранить</button><button type="button" className="secondary" onClick={() => setEditing(null)}>Отмена</button></div>
          </div>
        ) : null}
        <DataTable columns={[
          { key: "name", label: "Название" },
          { key: "channel", label: "Канал" },
          { key: "service_level_target", label: "Целевой SL", render: (row) => `${row.service_level_target}%` },
          { key: "target_answer_time_sec", label: "Ответ, сек" },
          { key: "is_active", label: "Статус", render: (row) => row.is_active ? "Активна" : "Отключена" },
          { key: "actions", label: "Действия", render: (row) => <div className="actions"><button type="button" onClick={() => selectQueue(row)}>Навыки</button><button type="button" className="secondary" onClick={() => openForm(row)}>Редактировать</button><button type="button" className="secondary" onClick={() => archiveQueue(row)}>Архивировать</button></div> }
        ]} rows={queues} emptyText="Создайте очереди вручную. Они нужны для загрузки нагрузки и расчёта потребности." />
      </section>
      <section className="panel">
        <PageHeader title="Навыки очереди" description={selectedQueue ? `Требования для очереди: ${String(selectedQueue.name)}` : "Выберите очередь в таблице выше."} />
        {selectedQueue ? (
          <>
            <div className="form-row">
              <select value={selectedSkillId} onChange={(event) => setSelectedSkillId(event.target.value)}>
                <option value="">Выберите навык</option>
                {skills.map((skill) => <option key={String(skill.id)} value={String(skill.id)}>{String(skill.name)}</option>)}
              </select>
              <input type="number" min="1" max="5" value={minLevel} onChange={(event) => setMinLevel(event.target.value)} />
              <button type="button" onClick={addSkill}>Добавить требование</button>
            </div>
            <DataTable columns={[
              { key: "skill_name", label: "Навык" },
              { key: "min_level", label: "Мин. уровень" },
              { key: "is_required", label: "Обязательный", render: (row) => row.is_required ? "да" : "нет" },
              { key: "actions", label: "Действия", render: (row) => <button type="button" className="secondary" onClick={() => removeSkill(row)}>Удалить</button> }
            ]} rows={queueSkills} />
          </>
        ) : null}
      </section>
    </>
  );
}
