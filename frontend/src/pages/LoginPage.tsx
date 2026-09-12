import { type FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../services/api";
import { Button, Field } from "../components/ui/Primitives";

const DEMOS = [
  { email: "manager@aniflow.ai", role: "Production Manager" },
  { email: "director@aniflow.ai", role: "Director" },
  { email: "artist@aniflow.ai", role: "Artist (Aki)" },
  { email: "reviewer@aniflow.ai", role: "Reviewer" },
  { email: "admin@aniflow.ai", role: "Admin" },
];

export function LoginPage() {
  const { user, login, loading } = useAuth();
  const [email, setEmail] = useState("manager@aniflow.ai");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (loading) return <p style={{ padding: 40, color: "var(--muted)" }}>Loading…</p>;
  if (user) return <Navigate to="/dashboard" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <section className="login-art">
        <div>
          <div className="brand-mark" style={{ marginBottom: 18 }}>
            あ
          </div>
          <h1 style={{ fontSize: 42, maxWidth: 420 }}>Production, visible from script to QC.</h1>
          <p style={{ marginTop: 16, maxWidth: 420, color: "#cbbfb0" }}>
            AniFlow AI helps studios track scenes, artist load, revisions, and risk — without replacing the artists who make the work.
          </p>
        </div>
        <p style={{ color: "#8d8276", fontSize: 13 }}>Northwind Animation · Project Sakura demo</p>
      </section>
      <section className="login-form">
        <form className="login-card" onSubmit={submit}>
          <h2>Sign in</h2>
          <p style={{ color: "var(--muted)", margin: 0 }}>Use a demo account or your studio credentials.</p>
          <Field label="Email">
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          </Field>
          <Field label="Password">
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required minLength={6} />
          </Field>
          {error && <p style={{ color: "var(--bad)", margin: 0 }}>{error}</p>}
          <Button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Enter studio"}
          </Button>
          <div className="row" style={{ flexWrap: "wrap" }}>
            {DEMOS.map((d) => (
              <button
                key={d.email}
                type="button"
                className="demo-chip"
                onClick={() => {
                  setEmail(d.email);
                  setPassword("demo1234");
                }}
              >
                {d.role}
              </button>
            ))}
          </div>
        </form>
      </section>
    </div>
  );
}
