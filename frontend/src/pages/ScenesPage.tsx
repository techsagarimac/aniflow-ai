import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge, Button, Card, EmptyState, ErrorState, Field, LoadingState, ProgressBar, Tabs } from "../components/ui/Primitives";
import { useAuth } from "../context/AuthContext";
import { useProject } from "../context/ProjectContext";
import { useToast } from "../context/ToastContext";
import { api, ApiError, getToken } from "../services/api";
import type { Comment, FileVersion, Review, Revision, Scene } from "../types";
import { KANBAN_COLUMNS } from "../types";
import { canDirect, canReview, formatDate, formatDateTime, labelize, toneFor } from "../utils/format";

export function ScenesPage() {
  const { projectId } = useProject();
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [tab, setTab] = useState("kanban");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const navigate = useNavigate();
  const { push } = useToast();

  const load = () => {
    if (!projectId) return;
    api
      .get<Scene[]>(`/api/scenes?project_id=${projectId}`)
      .then(setScenes)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  };
  useEffect(load, [projectId]);

  const move = async (id: number, column: string) => {
    try {
      const updated = await api.patch<Scene>(`/api/scenes/${id}`, { kanban_column: column });
      setScenes((rows) => rows.map((s) => (s.id === updated.id ? updated : s)));
    } catch (e) {
      push(e instanceof ApiError ? e.message : "Move failed", "err");
    }
  };

  if (error) return <ErrorState message={error} />;
  const visible = scenes.filter((s) => !filter || String(s.scene_number).includes(filter) || s.display_id.toLowerCase().includes(filter.toLowerCase()));

  return (
    <div>
      <div className="page-head">
        <div>
          <h2>Scenes</h2>
          <p>Drag cards between stages. Managers confirm every move.</p>
        </div>
        <input className="input" style={{ width: 200 }} placeholder="Filter SCN-042" value={filter} onChange={(e) => setFilter(e.target.value)} />
      </div>
      <Tabs tabs={[{ id: "kanban", label: "Kanban" }, { id: "list", label: "List" }]} value={tab} onChange={setTab} />
      {tab === "list" && (
        <Card>
          <table className="table">
            <thead><tr><th>ID</th><th>Ep</th><th>Stage</th><th>Artist</th><th>Priority</th><th>Due</th></tr></thead>
            <tbody>
              {visible.map((s) => (
                <tr key={s.id} onClick={() => navigate(`/scenes/${s.id}`)}>
                  <td>{s.display_id}</td>
                  <td>{s.episode_number}</td>
                  <td>{labelize(s.production_stage)}</td>
                  <td>{s.assigned_artist?.full_name ?? "—"}</td>
                  <td><Badge tone={toneFor(s.priority)}>{s.priority}</Badge></td>
                  <td>{formatDate(s.deadline)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
      {tab === "kanban" && (
        <div className="kanban">
          {KANBAN_COLUMNS.map((col) => (
            <div
              key={col.key}
              className="kanban-col"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                const id = Number(e.dataTransfer.getData("scene"));
                if (id) void move(id, col.key);
              }}
            >
              <h4>{col.label} ({visible.filter((s) => s.kanban_column === col.key).length})</h4>
              {visible
                .filter((s) => s.kanban_column === col.key)
                .map((s) => (
                  <article
                    key={s.id}
                    className="kanban-card"
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("scene", String(s.id))}
                    onClick={() => navigate(`/scenes/${s.id}`)}
                  >
                    <h5>{s.display_id}</h5>
                    <p style={{ color: "var(--muted)", fontSize: 12 }}>{s.description}</p>
                    <div className="row" style={{ marginTop: 6 }}>
                      <Badge tone={toneFor(s.priority)}>{s.priority}</Badge>
                      <span style={{ fontSize: 11 }}>{s.assigned_artist?.full_name ?? "Open"}</span>
                    </div>
                  </article>
                ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

type Rec = {
  recommended: { artist_id: number; name: string; reasons: string[]; score: number } | null;
  alternatives: Array<{ artist_id: number; name: string; reasons: string[] }>;
  disclaimer: string;
};

export function SceneDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const { push } = useToast();
  const [scene, setScene] = useState<Scene | null>(null);
  const [versions, setVersions] = useState<FileVersion[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [rec, setRec] = useState<Rec | null>(null);
  const [issue, setIssue] = useState("Character hand position is incorrect.");
  const [comment, setComment] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    if (!id) return;
    try {
      const s = await api.get<Scene>(`/api/scenes/${id}`);
      setScene(s);
      const [v, r, rev, c] = await Promise.all([
        api.get<FileVersion[]>(`/api/files/scene/${s.id}`),
        api.get<Review[]>(`/api/reviews?scene_id=${s.id}`),
        api.get<Revision[]>(`/api/revisions?scene_id=${s.id}`),
        api.get<Comment[]>(`/api/scenes/${s.id}/comments`),
      ]);
      setVersions(v);
      setReviews(r);
      setRevisions(rev);
      setComments(c);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed");
    }
  };
  useEffect(() => {
    void load();
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!scene) return <LoadingState />;

  const upload = async (file: File, markFinal = false) => {
    const form = new FormData();
    form.append("upload", file);
    form.append("notes", notes);
    form.append("mark_final", String(markFinal));
    await api.upload(`/api/files/scene/${scene.id}`, form);
    push("Version uploaded");
    await load();
  };

  return (
    <div className="stack">
      <div className="page-head">
        <div>
          <h2>{scene.display_id}</h2>
          <p>Episode {String(scene.episode_number).padStart(2, "0")} — {scene.episode_title}</p>
        </div>
        <Badge tone={toneFor(scene.production_stage)}>{labelize(scene.production_stage)}</Badge>
      </div>
      <div className="two">
        <Card>
          <p>{scene.description}</p>
          <p><strong>Location:</strong> {scene.location}</p>
          <p><strong>Characters:</strong> {scene.characters.map((c) => c.name).join(", ") || "—"}</p>
          <p><strong>Duration:</strong> {scene.duration_seconds}s · Priority {scene.priority}</p>
          <p><strong>Assigned:</strong> {scene.assigned_artist?.full_name ?? "Unassigned"}</p>
          <p><strong>Deadline:</strong> {formatDate(scene.deadline)}</p>
          <p><strong>Revisions:</strong> {scene.revision_count}</p>
          <ProgressBar value={scene.progress} />
        </Card>
        <Card>
          <h3>AI assignment recommendation</h3>
          <p className="ai-flag">Suggestion only. A manager must approve assignment.</p>
          {canDirect(user?.role || "") && (
            <Button size="sm" onClick={() => api.post<Rec>("/api/ai/assignment-recommendation", { scene_id: scene.id }).then(setRec)}>
              Recommend artist
            </Button>
          )}
          {rec?.recommended && (
            <div style={{ marginTop: 10 }}>
              <strong>{rec.recommended.name}</strong>
              <ul>{rec.recommended.reasons.map((r) => <li key={r}>{r}</li>)}</ul>
              <p>Alternatives: {rec.alternatives.map((a) => a.name).join(", ") || "None"}</p>
              {canDirect(user?.role || "") && rec.recommended.artist_id && (
                <Button
                  size="sm"
                  onClick={() =>
                    api.patch(`/api/scenes/${scene.id}`, { assigned_artist_id: rec.recommended!.artist_id }).then(() => {
                      push("Assignment approved by manager");
                      void load();
                    })
                  }
                >
                  Approve assignment
                </Button>
              )}
              <p className="ai-flag">{rec.disclaimer}</p>
            </div>
          )}
        </Card>
      </div>
      <Card>
        <h3>Version history</h3>
        {versions.length === 0 && <EmptyState title="No files yet" body="Artists upload storyboards, previews, and renders here. Prior versions are kept." />}
        <table className="table">
          <thead><tr><th>Version</th><th>Artist</th><th>Uploaded</th><th>Notes</th><th>Review</th><th></th></tr></thead>
          <tbody>
            {versions.map((v) => (
              <tr key={v.id} onClick={() => undefined}>
                <td>{v.label}</td>
                <td>{v.artist?.full_name}</td>
                <td>{formatDateTime(v.created_at)}</td>
                <td>{v.notes}</td>
                <td><Badge tone={toneFor(v.review_status)}>{labelize(v.review_status)}</Badge></td>
                <td>
                  {v.download_url && (
                    <a
                      href={v.download_url ?? "#"}
                      onClick={async (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        if (!v.download_url) return;
                        const res = await fetch(v.download_url, { headers: { Authorization: `Bearer ${getToken() ?? ""}` } });
                        const blob = await res.blob();
                        window.open(URL.createObjectURL(blob), "_blank");
                      }}
                    >
                      View
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {(user?.role === "artist" || canDirect(user?.role || "")) && (
          <div className="stack" style={{ marginTop: 12 }}>
            <Field label="Version notes"><input value={notes} onChange={(e) => setNotes(e.target.value)} /></Field>
            <input
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void upload(file);
              }}
            />
          </div>
        )}
      </Card>
      <div className="two">
        <Card>
          <h3>Reviews</h3>
          {reviews.map((r) => (
            <p key={r.id}><Badge tone={toneFor(r.status)}>{labelize(r.status)}</Badge> {r.reviewer?.full_name}: {r.comments}</p>
          ))}
          {canReview(user?.role || "") && (
            <div className="row">
              <Button size="sm" onClick={() => api.post("/api/reviews", { scene_id: scene.id, status: "approved", comments: "Approved for next stage" }).then(() => { push("Scene approved"); void load(); })}>Approve</Button>
              <Button size="sm" variant="secondary" onClick={() => api.post("/api/scenes/" + scene.id + "/advance", {}).then(() => { push("Moved to next stage"); void load(); })}>Advance stage</Button>
            </div>
          )}
        </Card>
        <Card>
          <h3>Revision requests</h3>
          {revisions.map((r) => (
            <div key={r.id} style={{ marginBottom: 8 }}>
              <strong>{r.issue}</strong>
              <p>{r.comment} · {r.assigned_to?.full_name} · <Badge>{r.status}</Badge></p>
            </div>
          ))}
          {canReview(user?.role || "") && (
            <div className="stack">
              <Field label="Issue"><input value={issue} onChange={(e) => setIssue(e.target.value)} /></Field>
              <Button size="sm" onClick={() => api.post("/api/revisions", { scene_id: scene.id, issue, comment: "Please correct and resubmit.", assigned_to_id: scene.assigned_artist_id }).then(() => { push("Revision requested"); void load(); })}>Request revision</Button>
            </div>
          )}
        </Card>
      </div>
      <Card>
        <h3>Comments</h3>
        {comments.map((c) => (
          <p key={c.id}><strong>{c.user?.full_name}:</strong> {c.body} <span className="ai-flag">{formatDateTime(c.created_at)}</span></p>
        ))}
        <div className="row">
          <input className="input" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Leave a note" />
          <Button
            onClick={() => {
              if (!comment.trim()) return;
              void api.post(`/api/scenes/${scene.id}/comments`, { body: comment }).then(() => {
                setComment("");
                void load();
              });
            }}
          >
            Send
          </Button>
        </div>
      </Card>
    </div>
  );
}
