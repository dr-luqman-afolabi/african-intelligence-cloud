"use client";
import { useState } from "react";
import { ragQuery, RAGSource } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: RAGSource[];
}

export default function ResearchPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await ragQuery({ query: userMsg.content, history });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to get a response. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <div className="border-b border-slate-200 bg-white px-6 py-4 flex items-center gap-3">
        <span className="text-2xl">🔬</span>
        <div>
          <h1 className="text-lg font-bold text-slate-800">AI Research Assistant</h1>
          <p className="text-xs text-slate-500">
            Powered by RAG over African economic indicators
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-4xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="text-center py-16 space-y-3">
            <div className="text-5xl">💬</div>
            <p className="text-slate-500 text-sm">
              Ask anything about African economic data, indicators, or trends.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              {[
                "What is the GDP growth trend in West Africa?",
                "Show me inflation data for East African countries",
                "Which countries have the best human development index?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="px-3 py-1.5 text-xs rounded-full border border-slate-300 bg-white hover:bg-slate-50 text-slate-600 transition"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm space-y-2 ${
                msg.role === "user"
                  ? "bg-aic-dark text-white rounded-br-none"
                  : "bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-sm"
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="border-t border-slate-100 pt-2 space-y-1">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
                    Sources
                  </p>
                  {msg.sources.map((src, j) => (
                    <div key={j} className="text-xs text-slate-500">
                      <span className="font-medium text-slate-700">{src.title}</span>
                      {" — "}
                      {src.excerpt}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none px-4 py-3 text-sm text-slate-400 shadow-sm">
              Thinking…
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-4">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about African economic data…"
            className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-aic-green"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-2.5 bg-aic-dark text-white text-sm rounded-xl font-medium hover:bg-slate-700 disabled:opacity-50 transition"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
