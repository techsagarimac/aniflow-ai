import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge, Button, Card, ErrorState, Field, LoadingState, Modal, ProgressBar, Tabs } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useProject } from "../context/ProjectContext";
import { useToast } from "../context/ToastContext";
import { api, ApiError } from "../services/api";
import type { Character, Episode, Project } from "../types";
import { canManage, formatDate, labelize, toneFor } from "../utils/format";

export function ProjectsPage() {
  const { projects, refresh } = useProject();
  const { user } = useAuth();
  const { push } = useToast();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>Projects</h2>
          <p>Studio shows currently on the board</p>
        </div>
        {user && canManage(user.role) && <Button onClick={() => setOpen(true)}>New project</Button>}
      </div>
      <div className="three">
        {projects.map((p) => (
          <Card key={p.id}>
            <div className="row" style={{ justifyContent: "space-between" }}>
              <h3>{p.name}</h3>
              <Badge tone={toneFor(p.status)}>{labelize(p.status)}</Badge>
            </div>
            <p style={{ color: "var(--muted)" }}>{p.studio} · {p.genre}</p>
            <ProgressBar value={p.overall_progress} />
            <p style={{ fontSize: 13 }}>{p.completed_episodes}/{p.episode_count} episodes · {p.overall_progress}%</p>
            <Button size="sm" variant="secondary" onClick={() => navigate(`/projects/${p.id}`)}>
              Open
            </Button>
          </Card>
        ))}
      </div>
      {open && (
        <ProjectModal
          onClose={() => setOpen(false)}
          onSaved={async () => {
            await refresh();
            setOpen(false);
            push("Project created");
          }}
        />
      )}
    </div>
  );
}

function ProjectModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [form, setForm] = useState({ name: "", description: "", genre: "slice of life", studio: "Northwind Animation", episode_count: 12, status: "planning" });
  const save = async () => {
    await api.post("/api/projects", form);
    onSaved();
  };
  return (
    <Modal title="New project" onClose={onClose}>
      <div className="stack">
        <Field label="Name"><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
        <Field label="Description"><textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
        <Field label="Genre"><input value={form.genre} onChange={(e) => setForm({ ...form, genre: e.target.value })} /></Field>
        <Button onClick={() => save().catch((e) => alert(e.message))}>Create</Button>
      </div>
    </Modal>
  );
}

export function ProjectDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [chars, setChars] = useState<Character[]>([]);
  const [tab, setTab] = useState("overview");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (!id) return;
    Promise.all([
      api.get<Project>(`/api/projects/${id}`),
      api.get<Episode[]>(`/api/episodes?project_id=${id}`),
      api.get<Character[]>(`/api/projects/${id}/characters`),
    ])
      .then(([p, e, c]) => {
        setProject(p);
        setEpisodes(e);
        setChars(c);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed"));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!project) return <LoadingState />;

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>{project.name}</h2>
          <p>{project.studio} · Director {project.director?.full_name} · PM {project.production_manager?.full_name}</p>
        </div>
        <Badge tone={toneFor(project.status)}>{labelize(project.status)}</Badge>
      </div>
      <Tabs
        tabs={[
          { id: "overview", label: "Overview" },
          { id: "episodes", label: "Episodes" },
          { id: "team", label: "Team" },
          { id: "analytics", label: "Analytics" },
        ]}
        value={tab}
        onChange={setTab}
      />
      {tab === "overview" && (
        <div className="two">
          <Card>
            <p>{project.description}</p>
            <p>Start {formatDate(project.start_date)} · Target {formatDate(project.target_completion_date)}</p>
            <ProgressBar value={project.overall_progress} />
          </Card>
          <Card>
            <h3>Characters</h3>
            {chars.map((c) => (
              <p key={c.id}><strong>{c.name}</strong> · {c.role}<br /><span style={{ color: "var(--muted)" }}>{c.description}</span></p>
            ))}
          </Card>
        </div>
      )}
      {tab === "episodes" && (
        <Card>
          <table className="table">
            <thead><tr><th>#</th><th>Title</th><th>Status</th><th>Progress</th><th>Risk</th></tr></thead>
            <tbody>
              {episodes.map((e) => (
                <tr key={e.id} onClick={() => navigate(`/episodes/${e.id}`)}>
                  <td>{String(e.number).padStart(2, "0")}</td>
                  <td>{e.title}</td>
                  <td><Badge tone={toneFor(e.status)}>{labelize(e.status)}</Badge></td>
                  <td><ProgressBar value={e.progress} /></td>
                  <td>{e.risk_level ? <Badge tone={toneFor(e.risk_level)}>{e.risk_level} {e.risk_score}</Badge> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {tab === "team" && (
        <Card>
          <p>Director: {project.director?.full_name}</p>
          <p>Production manager: {project.production_manager?.full_name}</p>
        </Card>
      )}
      {tab === "analytics" && (
        <Card>
          <Button onClick={() => navigate("/analytics")}>Open analytics workspace</Button>
        </Card>
      )}
    </div>
  );
}
