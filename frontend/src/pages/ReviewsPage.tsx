import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Badge, Card, ErrorState, LoadingState, Tabs } from "../components/ui/Primitives";
import { api, ApiError } from "../services/api";
import type { Review, Revision } from "../types";
import { formatDateTime, labelize, toneFor } from "../utils/format";

export function ReviewsPage() {
  const [tab, setTab] = useState("reviews");
  const [reviews, setReviews] = useState<Review[]>([]);
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([api.get<Review[]>("/api/reviews"), api.get<Revision[]>("/api/revisions")])
      .then(([a, b]) => {
        setReviews(a);
        setRevisions(b);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!reviews.length && !revisions.length && !error) return <LoadingState />;

  return (
    <div>
      <div className="page-head"><div><h2>Reviews & revisions</h2><p>Director and reviewer queue</p></div></div>
      <Tabs tabs={[{ id: "reviews", label: "Reviews" }, { id: "revisions", label: "Revision requests" }]} value={tab} onChange={setTab} />
      <Card>
        {tab === "reviews" ? (
          <table className="table">
            <thead><tr><th>Scene</th><th>Reviewer</th><th>Status</th><th>Notes</th><th>When</th></tr></thead>
            <tbody>
              {reviews.map((r) => (
                <tr key={r.id} onClick={() => navigate(`/scenes/${r.scene_id}`)}>
                  <td>#{r.scene_id}</td>
                  <td>{r.reviewer?.full_name}</td>
                  <td><Badge tone={toneFor(r.status)}>{labelize(r.status)}</Badge></td>
                  <td>{r.comments}</td>
                  <td>{formatDateTime(r.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="table">
            <thead><tr><th>Issue</th><th>Assigned</th><th>Priority</th><th>Status</th></tr></thead>
            <tbody>
              {revisions.map((r) => (
                <tr key={r.id} onClick={() => navigate(`/scenes/${r.scene_id}`)}>
                  <td>{r.issue}</td>
                  <td>{r.assigned_to?.full_name}</td>
                  <td><Badge tone={toneFor(r.priority)}>{r.priority}</Badge></td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
