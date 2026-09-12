export function labelize(value: string | null | undefined): string {
  if (!value) return "—";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

export function canManage(role: string) {
  return role === "admin" || role === "production_manager";
}

export function canDirect(role: string) {
  return canManage(role) || role === "director";
}

export function canReview(role: string) {
  return canDirect(role) || role === "reviewer";
}

export function toneFor(status: string): "neutral" | "good" | "warn" | "bad" | "info" {
  const v = status.toLowerCase();
  if (["completed", "approved", "low", "available"].includes(v)) return "good";
  if (["high", "revision", "overdue", "overloaded", "critical"].includes(v)) return "bad";
  if (["medium", "qc", "review", "pending", "busy"].includes(v)) return "warn";
  if (["animation", "production", "in_progress"].includes(v)) return "info";
  return "neutral";
}
