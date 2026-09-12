import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Badge, Card, ErrorState, LoadingState, ProgressBar } from "../components/ui/Primitives";
import { api, ApiError } from "../services/api";
import type { Artist, Scene } from "../types";
import { formatDate, labelize, toneFor } from "../utils/format";

export function ArtistsPage() {
  const [artists, setArtists] = useState<Artist[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    api.get<Artist[]>("/api/artists").then(setArtists).catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  }, []);
  if (error) return <ErrorState message={error} />;
  if (!artists.length) return <LoadingState />;
  return (
    <div>
      <div className="page-head"><div><h2>Artists</h2><p>Roster, skills, and current load</p></div></div>
      <Card>
        <table className="table">
          <thead><tr><th>Name</th><th>Role</th><th>Availability</th><th>Active</th><th>Load</th></tr></thead>
          <tbody>
            {artists.map((a) => (
              <tr key={a.id} onClick={() => navigate(`/artists/${a.user_id}`)}>
                <td>{a.user?.full_name}</td>
                <td>{labelize(a.artist_role)}</td>
                <td><Badge tone={toneFor(a.availability)}>{labelize(a.availability)}</Badge></td>
                <td>{a.active_tasks}</td>
                <td>{a.workload_percent}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

export function ArtistDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<{
    profile: Artist;
    active_scenes: Scene[];
    completed_scenes: Scene[];
    revision_total: number;
    avg_completion_hours: number;
  } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!id) return;
    api.get<typeof data>(`/api/artists/${id}`).then(setData).catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  }, [id]);
  if (error) return <ErrorState message={error} />;
  if (!data) return <LoadingState />;
  const p = data.profile;
  const chart = [
    { name: "Active", value: p.active_tasks },
    { name: "Completed", value: p.completed_tasks },
    { name: "Revisions", value: data.revision_total },
  ];
  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>{p.user?.full_name}</h2>
          <p>{labelize(p.artist_role)} · {labelize(p.experience_level)} · {p.skills.join(", ")}</p>
        </div>
        <Badge tone={toneFor(p.deadline_risk)}>{p.deadline_risk} deadline risk</Badge>
      </div>
      <div className="three">
        <Card className="stat"><h3>Workload</h3><strong>{p.workload_percent}%</strong><ProgressBar value={p.workload_percent} /></Card>
        <Card className="stat"><h3>Avg completion</h3><strong>{data.avg_completion_hours}h</strong></Card>
        <Card className="stat"><h3>Revisions</h3><strong>{data.revision_total}</strong></Card>
      </div>
      <Card style={{ height: 240 }}>
        <ResponsiveContainer>
          <BarChart data={chart}>
            <XAxis dataKey="name" stroke="currentColor" />
            <YAxis stroke="currentColor" />
            <Tooltip />
            <Bar dataKey="value" fill="#e07050" radius={6} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card>
        <h3>Active assignments</h3>
        <table className="table">
          <tbody>
            {data.active_scenes.map((s) => (
              <tr key={s.id} onClick={() => navigate(`/scenes/${s.id}`)}>
                <td>{s.display_id}</td>
                <td>{labelize(s.production_stage)}</td>
                <td>{formatDate(s.deadline)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
