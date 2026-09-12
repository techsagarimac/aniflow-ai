import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, EmptyState, ErrorState } from "../components/ui/Primitives";
import { api, ApiError } from "../services/api";
import type { Notification } from "../types";
import { formatDateTime } from "../utils/format";

export function NotificationsPage() {
  const [rows, setRows] = useState<Notification[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const load = () => api.get<Notification[]>("/api/notifications").then(setRows).catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  useEffect(() => {
    void load();
  }, []);

  if (error) return <ErrorState message={error} />;

  return (
    <div>
      <div className="page-head">
        <div><h2>Notifications</h2><p>Assignments, deadlines, revisions, and AI risk</p></div>
        <Button variant="secondary" onClick={() => api.post("/api/notifications/read-all").then(load)}>Mark all read</Button>
      </div>
      <Card>
        {rows.length === 0 && <EmptyState title="Inbox clear" body="You’ll see deadline and risk alerts here." />}
        {rows.map((n) => (
          <button
            key={n.id}
            type="button"
            className="btn btn-ghost"
            style={{ width: "100%", justifyContent: "space-between", opacity: n.is_read ? 0.65 : 1 }}
            onClick={() => {
              void api.post(`/api/notifications/${n.id}/read`);
              if (n.related_entity_type === "scene") navigate(`/scenes/${n.related_entity_id}`);
              if (n.related_entity_type === "episode") navigate(`/episodes/${n.related_entity_id}`);
            }}
          >
            <span>
              <strong>{n.title}</strong>
              <div style={{ color: "var(--muted)", fontWeight: 400 }}>{n.message}</div>
            </span>
            <span>{formatDateTime(n.created_at)}</span>
          </button>
        ))}
      </Card>
    </div>
  );
}

export function SettingsPage() {
  return (
    <div className="stack">
      <div className="page-head"><div><h2>Settings</h2><p>Studio preferences for this demo environment</p></div></div>
      <Card>
        <p>Theme is toggled from the top bar. AI provider is configured with <code>AI_API_KEY</code> / <code>AI_PROVIDER</code> on the backend. With no key, Mock AI stays on so the product remains fully usable.</p>
        <p>Demo password for all seeded accounts: <code>demo1234</code></p>
      </Card>
    </div>
  );
}
