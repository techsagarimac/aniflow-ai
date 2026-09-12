import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Badge, Card, LoadingState, ErrorState, ProgressBar, Avatar, Button } from "../components/ui/Primitives";
import { useProject } from "../context/ProjectContext";
import { api, ApiError } from "../services/api";
import type { DashboardData } from "../types";
import { formatDate, labelize, toneFor } from "../utils/format";

const STAGE_ORDER = [
  "script",
  "storyboard",
  "layout",
  "key_animation",
  "in_between",
  "background",
  "coloring",
  "compositing",
  "qc",
];

export function DashboardPage() {
  const { projectId } = useProject();
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    api
      .get<DashboardData>(`/api/dashboard?project_id=${projectId}`)
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;
  if (!data) return null;
  const m = data.metrics;
  const ep7 = data.episodes.find((e) => e.number === 7);

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>Production overview</h2>
          <p>Project Sakura · live board for the current lock window</p>
        </div>
        {ep7 && (
          <Button variant="secondary" onClick={() => navigate(`/episodes/${ep7.id}`)}>
            Open Episode 07
          </Button>
        )}
      </div>
      <div className="grid-stats">
        <Card className="stat">
          <h3>Episodes</h3>
          <strong>{m.completed_episodes}/{m.total_episodes}</strong>
          <span>{m.episodes_in_production} in production</span>
        </Card>
        <Card className="stat">
          <h3>Overall</h3>
          <strong>{m.overall_progress}%</strong>
          <ProgressBar value={m.overall_progress} />
        </Card>
        <Card className="stat">
          <h3>Scenes</h3>
          <strong>{m.completed_scenes}/{m.total_scenes}</strong>
          <span>{m.scenes_in_production} active</span>
        </Card>
        <Card className="stat">
          <h3>Overdue</h3>
          <strong>{m.overdue_scenes}</strong>
          <span>scenes past deadline</span>
        </Card>
      </div>
      <div className="two">
        <Card>
          <h3 style={{ marginBottom: 12 }}>Production progress</h3>
          <div className="stack">
            {STAGE_ORDER.map((key) => {
              const row = data.stage_progress[key];
              return (
                <div key={key}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 4 }}>
                    <span>{labelize(key)}</span>
                    <span style={{ color: "var(--muted)" }}>{row?.percent ?? 0}%</span>
                  </div>
                  <ProgressBar value={row?.percent ?? 0} />
                </div>
              );
            })}
          </div>
        </Card>
        <div className="stack">
          <Card>
            <h3 style={{ marginBottom: 12 }}>Current bottlenecks</h3>
            {data.bottlenecks.map((b) => (
              <div key={b.episode_id} className="card" style={{ boxShadow: "none", marginBottom: 8 }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <strong>
                    Episode {String(b.episode_number).padStart(2, "0")} — {b.episode_title}
                  </strong>
                  <Badge tone={toneFor(b.risk_level)}>{b.risk_level} · {b.risk_score}</Badge>
                </div>
                <p style={{ color: "var(--muted)", margin: "8px 0" }}>{b.reason}</p>
                <p style={{ margin: "0 0 8px" }}>Predicted delay: {b.predicted_delay} · AI estimate</p>
                <Button size="sm" onClick={() => navigate(`/episodes/${b.episode_id}`)}>
                  Review recommendation
                </Button>
              </div>
            ))}
          </Card>
          <Card>
            <h3 style={{ marginBottom: 12 }}>Upcoming deadlines</h3>
            <table className="table">
              <tbody>
                {data.upcoming_deadlines.map((d) => (
                  <tr key={d.id} onClick={() => d.episode_id && navigate(`/episodes/${d.episode_id}`)}>
                    <td>{d.title}</td>
                    <td>{formatDate(d.due_date)}</td>
                    <td>
                      <Badge tone={toneFor(d.status)}>{d.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      </div>
      <Card>
        <h3 style={{ marginBottom: 12 }}>Artist workload</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Artist</th>
              <th>Role</th>
              <th>Active tasks</th>
              <th>Workload</th>
              <th>Deadline risk</th>
            </tr>
          </thead>
          <tbody>
            {data.artist_workload.map((a) => (
              <tr key={a.user_id} onClick={() => navigate(`/artists/${a.user_id}`)}>
                <td>
                  <span className="row">
                    <Avatar name={a.name} color={a.avatar_color} size={28} /> {a.name}
                  </span>
                </td>
                <td>{labelize(a.role)}</td>
                <td>{a.active_tasks}</td>
                <td style={{ minWidth: 140 }}>
                  <ProgressBar value={Math.min(a.workload_percent, 120)} />
                  <span style={{ fontSize: 12, color: "var(--muted)" }}>{a.workload_percent}%</span>
                </td>
                <td>
                  <Badge tone={toneFor(a.deadline_risk)}>{a.deadline_risk}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
