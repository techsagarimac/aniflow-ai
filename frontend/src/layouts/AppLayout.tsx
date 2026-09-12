import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Bell,
  CalendarDays,
  Clapperboard,
  Film,
  LayoutDashboard,
  LayoutGrid,
  ListTodo,
  MessageSquare,
  Search,
  Settings,
  Sparkles,
  SunMoon,
  Users,
  BarChart3,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useProject } from "../context/ProjectContext";
import { useToast } from "../context/ToastContext";
import { api } from "../services/api";
import { Avatar } from "../components/ui/Primitives";
import type { Notification, Scene, Task } from "../types";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/projects", label: "Projects", icon: Clapperboard },
  { to: "/episodes", label: "Episodes", icon: Film },
  { to: "/scenes", label: "Scenes", icon: LayoutGrid },
  { to: "/tasks", label: "Tasks", icon: ListTodo },
  { to: "/artists", label: "Artists", icon: Users },
  { to: "/calendar", label: "Production Calendar", icon: CalendarDays },
  { to: "/reviews", label: "Reviews", icon: Sparkles },
  { to: "/assistant", label: "AI Assistant", icon: MessageSquare },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const { projects, projectId, setProjectId } = useProject();
  const { toasts, dismiss } = useToast();
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => localStorage.getItem("aniflow_theme") || "dark");
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<{ scenes: Scene[]; episodes: { id: number; number: number; title: string }[]; tasks: Task[] } | null>(null);
  const [notes, setNotes] = useState<Notification[]>([]);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("aniflow_theme", theme);
  }, [theme]);

  useEffect(() => {
    api.get<Notification[]>("/api/notifications").then(setNotes).catch(() => setNotes([]));
  }, []);

  useEffect(() => {
    if (q.trim().length < 2) {
      setHits(null);
      return;
    }
    const t = window.setTimeout(() => {
      const params = new URLSearchParams({ q });
      if (projectId) params.set("project_id", String(projectId));
      api
        .get<{ scenes: Scene[]; episodes: { id: number; number: number; title: string }[]; tasks: Task[] }>(`/api/search?${params}`)
        .then(setHits)
        .catch(() => setHits(null));
    }, 220);
    return () => window.clearTimeout(t);
  }, [q, projectId]);

  const unread = notes.filter((n) => !n.is_read).length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">あ</div>
          <div>
            <h1>AniFlow AI</h1>
            <small>Studio production</small>
          </div>
        </div>
        <nav className="nav">
          {NAV.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                <Icon size={16} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">
          <div className="search" ref={searchRef}>
            <Search size={16} style={{ position: "absolute", left: 12, top: 11, color: "var(--muted)" }} />
            <input placeholder="Search scenes, episodes, tasks" value={q} onChange={(e) => setQ(e.target.value)} />
            {hits && (
              <div className="search-pop">
                {hits.scenes.map((s) => (
                  <button
                    key={s.id}
                    className="btn btn-ghost btn-sm"
                    type="button"
                    onClick={() => {
                      navigate(`/scenes/${s.id}`);
                      setQ("");
                      setHits(null);
                    }}
                  >
                    {s.display_id} · {s.location}
                  </button>
                ))}
                {hits.episodes.map((e) => (
                  <button
                    key={e.id}
                    className="btn btn-ghost btn-sm"
                    type="button"
                    onClick={() => {
                      navigate(`/episodes/${e.id}`);
                      setQ("");
                      setHits(null);
                    }}
                  >
                    EP{String(e.number).padStart(2, "0")} {e.title}
                  </button>
                ))}
                {!hits.scenes.length && !hits.episodes.length && !hits.tasks.length && <p className="empty">No matches</p>}
              </div>
            )}
          </div>
          <select
            className="input"
            style={{ width: 220 }}
            value={projectId ?? ""}
            onChange={(e) => setProjectId(Number(e.target.value))}
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => navigate("/notifications")}>
            <Bell size={16} /> {unread || ""}
          </button>
          <button className="btn btn-ghost btn-sm" type="button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
            <SunMoon size={16} />
          </button>
          <div className="row" style={{ gap: 8 }}>
            {user && <Avatar name={user.full_name} color={user.avatar_color} />}
            <div>
              <div style={{ fontSize: 13, fontWeight: 650 }}>{user?.full_name}</div>
              <div style={{ fontSize: 11, color: "var(--muted)", textTransform: "capitalize" }}>{user?.role.replaceAll("_", " ")}</div>
            </div>
            <button className="btn btn-secondary btn-sm" type="button" onClick={logout}>
              Log out
            </button>
          </div>
        </header>
        <div className="content">
          <Outlet />
        </div>
      </div>
      <div className="toast-stack">
        {toasts.map((t) => (
          <button key={t.id} className={`toast ${t.tone === "err" ? "err" : ""}`} type="button" onClick={() => dismiss(t.id)}>
            {t.title}
          </button>
        ))}
      </div>
    </div>
  );
}
