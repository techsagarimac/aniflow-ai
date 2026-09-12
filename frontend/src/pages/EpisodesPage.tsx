import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge, Button, Card, ErrorState, LoadingState, ProgressBar } from "../components/ui/Primitives";
import { useProject } from "../context/ProjectContext";
import { useToast } from "../context/ToastContext";
import { api, ApiError } from "../services/api";
import type { Episode, Scene } from "../types";
import { formatDate, labelize, toneFor } from "../utils/format";

export function EpisodesPage() {
  const { projectId } = useProject();
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (!projectId) return;
    api
      .get<Episode[]>(`/api/episodes?project_id=${projectId}`)
      .then(setEpisodes)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  }, [projectId]);

  if (error) return <ErrorState message={error} />;
  if (!episodes.length && !error) return <LoadingState />;

  return (
    <div>
      <div className="page-head"><div><h2>Episodes</h2><p>Twelve-episode lock plan for the current project</p></div></div>
      <Card>
        <table className="table">
          <thead><tr><th>Ep</th><th>Title</th><th>Status</th><th>Scenes</th><th>Revisions</th><th>Progress</th><th>Risk</th></tr></thead>
          <tbody>
            {episodes.map((e) => (
              <tr key={e.id} onClick={() => navigate(`/episodes/${e.id}`)}>
                <td>{String(e.number).padStart(2, "0")}</td>
                <td>{e.title}</td>
                <td><Badge tone={toneFor(e.status)}>{labelize(e.status)}</Badge></td>
                <td>{e.scene_count}</td>
                <td>{e.revision_count}</td>
                <td style={{ minWidth: 120 }}><ProgressBar value={e.progress} /></td>
                <td>{e.risk_level ? <Badge tone={toneFor(e.risk_level)}>{labelize(e.risk_level)}</Badge> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

type Schedule = {
  is_ai_estimate: boolean;
  disclaimer: string;
  estimated_working_days: number;
  stages: Record<string, { days: number }>;
};

type Bottleneck = {
  is_ai_estimate?: boolean;
  bottlenecks: Array<{
    stage: string;
    reason: string;
    predicted_delay: string;
    recommended_action: string;
    requires_manager_approval?: boolean;
    risk_level?: string;
    artist_workload?: number;
  }>;
};

type Risk = {
  is_ai_estimate: boolean;
  disclaimer: string;
  risk_score: number;
  risk_level: string;
  factors: Record<string, number>;
  recommendations: string[];
  predicted_delay_days: string;
};

export function EpisodeDetailPage() {
  const { id } = useParams();
  const { push } = useToast();
  const navigate = useNavigate();
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [schedule, setSchedule] = useState<Schedule | null>(null);
  const [bottleneck, setBottleneck] = useState<Bottleneck | null>(null);
  const [risk, setRisk] = useState<Risk | null>(null);
  const [error, setError] = useState("");
  const [analysisId, setAnalysisId] = useState<number | null>(null);

  const load = () => {
    if (!id) return;
    Promise.all([api.get<Episode>(`/api/episodes/${id}`), api.get<Scene[]>(`/api/scenes?episode_id=${id}`)])
      .then(([e, s]) => {
        setEpisode(e);
        setScenes(s);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed"));
  };

  useEffect(load, [id]);

  if (error) return <ErrorState message={error} />;
  if (!episode) return <LoadingState />;

  const runSchedule = async () => {
    const res = await api.post<Schedule>("/api/ai/schedule", { episode_id: episode.id });
    setSchedule(res);
  };
  const runBottleneck = async () => {
    const res = await api.post<Bottleneck>("/api/ai/bottlenecks", { episode_id: episode.id });
    setBottleneck(res);
    const rows = await api.get<Array<{ id: number; analysis_type: string }>>(`/api/ai/analyses?episode_id=${episode.id}`);
    const last = rows.find((r) => r.analysis_type === "bottleneck");
    if (last) setAnalysisId(last.id);
  };
  const runRisk = async () => {
    const res = await api.post<Risk>("/api/ai/risk-analysis", { episode_id: episode.id });
    setRisk(res);
  };

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>Episode {String(episode.number).padStart(2, "0")} — {episode.title}</h2>
          <p>{episode.description}</p>
        </div>
        <div className="row">
          <Badge tone={toneFor(episode.status)}>{labelize(episode.status)}</Badge>
          {episode.risk_level && <Badge tone={toneFor(episode.risk_level)}>{episode.risk_level} {episode.risk_score}/100</Badge>}
        </div>
      </div>
      {episode.number === 7 && (
        <Card>
          <strong>High-risk warning (AI estimate)</strong>
          <p>Animation is overloaded. Open bottleneck analysis before redistributing work.</p>
        </Card>
      )}
      <div className="three">
        <Card className="stat"><h3>Progress</h3><strong>{episode.progress}%</strong><ProgressBar value={episode.progress} /></Card>
        <Card className="stat"><h3>Scenes</h3><strong>{episode.scene_count}</strong></Card>
        <Card className="stat"><h3>Revisions</h3><strong>{episode.revision_count}</strong></Card>
      </div>
      <div className="two">
        <Card>
          <h3>Scene list</h3>
          <table className="table">
            <thead><tr><th>ID</th><th>Stage</th><th>Artist</th><th>Due</th></tr></thead>
            <tbody>
              {scenes.map((s) => (
                <tr key={s.id} onClick={() => navigate(`/scenes/${s.id}`)}>
                  <td>{s.display_id}</td>
                  <td><Badge tone={toneFor(s.production_stage)}>{labelize(s.production_stage)}</Badge></td>
                  <td>{s.assigned_artist?.full_name ?? "Unassigned"}</td>
                  <td>{formatDate(s.deadline)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <div className="stack">
          <Card>
            <h3>AI schedule estimate</h3>
            <p className="ai-flag">Never treated as a guaranteed date.</p>
            <Button size="sm" onClick={() => runSchedule().catch((e) => push(e.message, "err"))}>Estimate completion</Button>
            {schedule && (
              <div style={{ marginTop: 12 }}>
                {Object.entries(schedule.stages).map(([k, v]) => (
                  <div key={k} className="row" style={{ justifyContent: "space-between" }}>
                    <span>{labelize(k)}</span><strong>{v.days} days</strong>
                  </div>
                ))}
                <p>Estimated completion: {schedule.estimated_working_days} working days</p>
                <p className="ai-flag">{schedule.disclaimer}</p>
              </div>
            )}
          </Card>
          <Card>
            <h3>Bottleneck analysis</h3>
            <Button size="sm" onClick={() => runBottleneck().catch((e) => push(e.message, "err"))}>Analyze bottlenecks</Button>
            {bottleneck?.bottlenecks.map((b, i) => (
              <div key={i} style={{ marginTop: 10 }}>
                <Badge tone={toneFor(b.risk_level || "medium")}>{b.risk_level}</Badge>
                <p>{b.reason}</p>
                <p>Predicted delay: {b.predicted_delay}</p>
                <p>{b.recommended_action}</p>
                {b.requires_manager_approval && analysisId && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() =>
                      api.post(`/api/ai/analyses/${analysisId}/approve`, { approved: true }).then(() => push("Recommendation recorded. Work was not auto-reassigned."))
                    }
                  >
                    Manager approve recommendation
                  </Button>
                )}
              </div>
            ))}
          </Card>
          <Card>
            <h3>Production risk score</h3>
            <Button size="sm" onClick={() => runRisk().catch((e) => push(e.message, "err"))}>Recalculate risk</Button>
            {risk && (
              <div>
                <strong style={{ fontSize: 32 }}>{risk.risk_score}/100</strong>
                <Badge tone={toneFor(risk.risk_level)}>{risk.risk_level}</Badge>
                {Object.entries(risk.factors).map(([k, v]) => (
                  <div key={k}><span>{labelize(k)}</span><ProgressBar value={v} /></div>
                ))}
                <p className="ai-flag">{risk.disclaimer}</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
