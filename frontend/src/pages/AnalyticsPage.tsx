import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, ErrorState, Field, LoadingState } from "../components/ui/Primitives";
import { useProject } from "../context/ProjectContext";
import { api, ApiError } from "../services/api";

type Analytics = {
  progress_over_time: { week: string; completed: number; progress: number }[];
  scenes_completed_per_week: { week: string; completed: number }[];
  avg_scene_completion_hours: number;
  revision_frequency: { label: string; revisions: number }[];
  artist_workload: { name: string; workload: number }[];
  episode_completion: { episode: string; progress: number; status: string }[];
  stage_bottlenecks: { stage: string; count: number; percent: number }[];
  on_time_rate: number;
  ai_risk_trends: { label: string; score: number; level: string }[];
};

export function AnalyticsPage() {
  const { projectId } = useProject();
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState("");
  const [artistId, setArtistId] = useState("");

  useEffect(() => {
    const params = new URLSearchParams();
    if (projectId) params.set("project_id", String(projectId));
    if (artistId) params.set("artist_id", artistId);
    api.get<Analytics>(`/api/analytics?${params}`).then(setData).catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  }, [projectId, artistId]);

  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;

  return (
    <div className="stack">
      <div className="page-head">
        <div><h2>Analytics</h2><p>On-time rate {data.on_time_rate}% · avg scene {data.avg_scene_completion_hours}h</p></div>
        <Field label="Artist filter">
          <input className="input" placeholder="Artist user id" value={artistId} onChange={(e) => setArtistId(e.target.value)} />
        </Field>
      </div>
      <div className="two">
        <Card style={{ height: 280 }}>
          <h3>Production progress over time</h3>
          <ResponsiveContainer>
            <LineChart data={data.progress_over_time}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
              <XAxis dataKey="week" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="progress" stroke="#e07050" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card style={{ height: 280 }}>
          <h3>Scenes completed per week</h3>
          <ResponsiveContainer>
            <BarChart data={data.scenes_completed_per_week}>
              <XAxis dataKey="week" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="completed" fill="#7ea3c0" radius={6} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="two">
        <Card style={{ height: 280 }}>
          <h3>Artist workload</h3>
          <ResponsiveContainer>
            <BarChart data={data.artist_workload} layout="vertical">
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={90} />
              <Tooltip />
              <Bar dataKey="workload" fill="#c45c3e" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card style={{ height: 280 }}>
          <h3>Episode completion</h3>
          <ResponsiveContainer>
            <BarChart data={data.episode_completion}>
              <XAxis dataKey="episode" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="progress" fill="#3ddc97" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <div className="two">
        <Card style={{ height: 280 }}>
          <h3>Stage bottlenecks</h3>
          <ResponsiveContainer>
            <BarChart data={data.stage_bottlenecks}>
              <XAxis dataKey="stage" hide />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#f0b45a" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card style={{ height: 280 }}>
          <h3>AI risk trends</h3>
          <ResponsiveContainer>
            <BarChart data={data.ai_risk_trends}>
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#ff6b81" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
      <Card>
        <h3>Revision frequency</h3>
        <table className="table">
          <tbody>
            {data.revision_frequency.map((r) => (
              <tr key={r.label}><td>{r.label}</td><td>{r.revisions}</td></tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
