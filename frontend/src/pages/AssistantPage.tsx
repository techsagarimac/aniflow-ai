import { useState } from "react";
import { Button } from "../components/ui/Primitives";
import { useProject } from "../context/ProjectContext";
import { api } from "../services/api";

const PROMPTS = [
  "Which episodes are at risk?",
  "Which artists are overloaded?",
  "How many scenes are waiting for review?",
  "Why is Episode 7 delayed?",
  "Which scenes should we prioritize?",
  "Estimate completion for Episode 8.",
  "Show me overdue tasks.",
];

export function AssistantPage() {
  const { projectId } = useProject();
  const [input, setInput] = useState("Which episodes are at risk?");
  const [messages, setMessages] = useState<Array<{ role: "user" | "bot"; text: string }>>([
    { role: "bot", text: "AniFlow Assistant answers from this project's production database — scenes, artists, risk, and queues. I will not reassign work." },
  ]);
  const [busy, setBusy] = useState(false);

  const send = async (text: string) => {
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const res = await api.post<{ answer: string; is_ai_estimate: boolean }>("/api/ai/chat", { message: text, project_id: projectId });
      setMessages((m) => [...m, { role: "bot", text: res.answer + (res.is_ai_estimate ? "\n\n(AI estimate based on current production data.)" : "") }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "bot", text: e instanceof Error ? e.message : "Assistant unavailable" }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="chat">
      <div className="page-head"><div><h2>AniFlow Assistant</h2><p>Grounded in Project Sakura — not a generic chatbot</p></div></div>
      <div className="row" style={{ flexWrap: "wrap", marginBottom: 10 }}>
        {PROMPTS.map((p) => (
          <button key={p} className="demo-chip" type="button" onClick={() => { setInput(p); void send(p); }}>{p}</button>
        ))}
      </div>
      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>{m.text}</div>
        ))}
      </div>
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          if (!input.trim() || busy) return;
          const t = input;
          setInput("");
          void send(t);
        }}
      >
        <input className="input" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about risk, load, or Episode 07…" />
        <Button type="submit" disabled={busy}>{busy ? "Thinking…" : "Send"}</Button>
      </form>
    </div>
  );
}
