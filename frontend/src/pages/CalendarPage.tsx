import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorState, LoadingState } from "../components/ui/Primitives";
import { useProject } from "../context/ProjectContext";
import { api, ApiError } from "../services/api";
import type { CalendarEvent } from "../types";

export function CalendarPage() {
  const { projectId } = useProject();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const q = projectId ? `?project_id=${projectId}` : "";
    setLoading(true);
    api.get<{ events: CalendarEvent[] }>(`/api/calendar${q}`).then((r) => setEvents(r.events)).catch((e) => setError(e instanceof ApiError ? e.message : "Failed")).finally(() => setLoading(false));
  }, [projectId]);

  const cells = useMemo(() => {
    const month = new Date(2026, 8, 1);
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const startPad = first.getDay();
    const days = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    return Array.from({ length: startPad + days }, (_, i) => {
      if (i < startPad) return null;
      return new Date(month.getFullYear(), month.getMonth(), i - startPad + 1);
    });
  }, []);

  if (error) return <ErrorState message={error} />;
  if (loading) return <LoadingState />;

  return (
    <div>
      <div className="page-head"><div><h2>Production calendar</h2><p>September 2026 · scene locks, reviews, and milestones</p></div></div>
      <div className="calendar-grid" style={{ marginBottom: 8 }}>
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => <div key={d} style={{ color: "var(--muted)", fontSize: 12 }}>{d}</div>)}
      </div>
      <div className="calendar-grid">
        {cells.map((d, i) => {
          if (!d) return <div key={`e${i}`} />;
          const key = d.toISOString().slice(0, 10);
          const items = events.filter((ev) => ev.date.slice(0, 10) === key);
          return (
            <div key={key} className="cal-cell">
              <strong>{d.getDate()}</strong>
              {items.slice(0, 3).map((ev) => (
                <div
                  key={ev.id}
                  className="ev"
                  onClick={() => {
                    if (ev.entity_type === "scene") navigate(`/scenes/${ev.entity_id}`);
                    else if (ev.entity_type === "episode") navigate(`/episodes/${ev.entity_id}`);
                    else if (ev.scene_id) navigate(`/scenes/${ev.scene_id}`);
                    else if (ev.episode_id) navigate(`/episodes/${ev.episode_id}`);
                  }}
                >
                  {ev.title}
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
