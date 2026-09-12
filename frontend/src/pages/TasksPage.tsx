import { useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, ErrorState, Field, LoadingState, Modal, Tabs } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useProject } from "../context/ProjectContext";
import { useToast } from "../context/ToastContext";
import { api, ApiError } from "../services/api";
import type { Task, User } from "../types";
import { canDirect, formatDate, labelize, toneFor } from "../utils/format";

const COLUMNS = ["todo", "in_progress", "review", "revision", "approved", "completed"];

export function TasksPage() {
  const { projectId } = useProject();
  const { user } = useAuth();
  const { push } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tab, setTab] = useState("list");
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [users, setUsers] = useState<User[]>([]);

  const load = () => {
    if (!projectId) return;
    api.get<Task[]>(`/api/tasks?project_id=${projectId}`).then(setTasks).catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  };
  useEffect(load, [projectId]);
  useEffect(() => {
    api.get<User[]>("/api/users").then(setUsers).catch(() => setUsers([]));
  }, []);

  const move = (id: number, status: string) => {
    api.patch<Task>(`/api/tasks/${id}`, { status }).then((updated) => setTasks((rows) => rows.map((t) => (t.id === updated.id ? updated : t))));
  };

  const monthDays = useMemo(() => {
    const start = new Date(2026, 8, 1);
    return Array.from({ length: 30 }, (_, i) => new Date(start.getFullYear(), start.getMonth(), i + 1));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!tasks.length && !error) return <LoadingState />;

  return (
    <div>
      <div className="page-head">
        <div><h2>Tasks</h2><p>Work items linked to scenes and artists</p></div>
        {user && canDirect(user.role) && <Button onClick={() => setOpen(true)}>New task</Button>}
      </div>
      <Tabs tabs={[{ id: "list", label: "List" }, { id: "kanban", label: "Kanban" }, { id: "calendar", label: "Calendar" }]} value={tab} onChange={setTab} />
      {tab === "list" && (
        <Card>
          <table className="table">
            <thead><tr><th>Title</th><th>Type</th><th>Assignee</th><th>Status</th><th>Due</th></tr></thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} onClick={() => undefined}>
                  <td>{t.title}</td>
                  <td>{labelize(t.type)}</td>
                  <td>{t.assignee?.full_name ?? "—"}</td>
                  <td>
                    <select className="input" value={t.status} onChange={(e) => move(t.id, e.target.value)}>
                      {COLUMNS.map((c) => <option key={c} value={c}>{labelize(c)}</option>)}
                    </select>
                  </td>
                  <td>{formatDate(t.deadline)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {tab === "kanban" && (
        <div className="kanban" style={{ gridTemplateColumns: "repeat(6, minmax(160px,1fr))" }}>
          {COLUMNS.map((col) => (
            <div key={col} className="kanban-col">
              <h4>{labelize(col)}</h4>
              {tasks.filter((t) => t.status === col).map((t) => (
                <article key={t.id} className="kanban-card">
                  <h5>{t.title}</h5>
                  <p style={{ fontSize: 12 }}>{t.assignee?.full_name}</p>
                  <Badge tone={toneFor(t.priority)}>{t.priority}</Badge>
                </article>
              ))}
            </div>
          ))}
        </div>
      )}
      {tab === "calendar" && (
        <div className="calendar-grid">
          {monthDays.map((d) => {
            const key = d.toISOString().slice(0, 10);
            const items = tasks.filter((t) => t.deadline === key);
            return (
              <div key={key} className="cal-cell">
                <strong>{d.getDate()}</strong>
                {items.slice(0, 3).map((t) => <div key={t.id} className="ev">{t.title}</div>)}
              </div>
            );
          })}
        </div>
      )}
      {open && (
        <Modal title="Create task" onClose={() => setOpen(false)}>
          <TaskForm
            users={users}
            projectId={projectId}
            onCreate={(payload) =>
              api.post("/api/tasks", payload).then(() => {
                push("Task created");
                setOpen(false);
                load();
              })
            }
          />
        </Modal>
      )}
    </div>
  );
}

function TaskForm({ users, projectId, onCreate }: { users: User[]; projectId: number | null; onCreate: (p: Record<string, unknown>) => void }) {
  const [title, setTitle] = useState("");
  const [assignee, setAssignee] = useState<number | "">("");
  return (
    <div className="stack">
      <Field label="Title"><input value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
      <Field label="Assignee">
        <select value={assignee} onChange={(e) => setAssignee(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Unassigned</option>
          {users.filter((u) => u.role === "artist").map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
        </select>
      </Field>
      <Button onClick={() => onCreate({ project_id: projectId, title, assignee_id: assignee || null, type: "general", estimated_hours: 6 })}>Save</Button>
    </div>
  );
}
