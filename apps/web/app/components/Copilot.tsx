"use client";

import { FormEvent, useState } from "react";
import { apiFetch } from "../api";
import { Icon } from "./Icons";

type CopilotResponse = {
  answer: string;
  mode: string;
  model?: string | null;
  tool_calls: Array<{ name: string; source_id: string }>;
  citations: Array<{ id: string; label: string; as_of: string }>;
  limitations: string[];
};

const prompts = [
  "Why did this portfolio underperform its benchmark?",
  "How concentrated is this portfolio?",
  "Which scenario produces the largest estimated loss?",
];

function FormattedAnswer({ text }: { text: string }) {
  return (
    <p>
      {text.split("**").map((part, index) =>
        index % 2 ? <strong key={index}>{part}</strong> : <span key={index}>{part}</span>,
      )}
    </p>
  );
}

export function Copilot({ portfolioId }: { portfolioId: string }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function ask(event?: FormEvent) {
    event?.preventDefault();
    if (!question.trim() || loading) return;
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<CopilotResponse>("/api/copilot/questions", {
        method: "POST",
        body: JSON.stringify({ portfolio_id: portfolioId, question }),
      });
      setResponse(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Copilot request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-panel" aria-labelledby="copilot-heading">
      <div className="copilot-head">
        <div className="copilot-badge"><Icon name="copilot" size={20} /></div>
        <div>
          <div className="eyebrow light">RESEARCH ASSISTANT</div>
          <h2 id="copilot-heading">Portfolio Copilot</h2>
        </div>
        <span className="grounded-pill"><i /> Grounded</span>
      </div>
      <div className="copilot-body">
        {!response && (
          <>
            <p className="copilot-intro">
              Ask about performance, concentration, drawdowns, or deterministic scenarios.
              Every number comes from a read-only analytics tool.
            </p>
            <div className="suggestions">
              {prompts.map((prompt) => (
                <button key={prompt} onClick={() => setQuestion(prompt)}>{prompt}</button>
              ))}
            </div>
          </>
        )}
        {response && (
          <div className="copilot-response">
            <FormattedAnswer text={response.answer} />
            {response.tool_calls.length > 0 && (
              <details>
                <summary><Icon name="shield" size={15} /> {response.tool_calls.length} verified tool call{response.tool_calls.length > 1 ? "s" : ""}</summary>
                <div className="tool-list">
                  {response.tool_calls.map((call) => (
                    <div key={call.source_id}>
                      <code>{call.name}</code>
                      <small>{call.source_id}</small>
                    </div>
                  ))}
                </div>
              </details>
            )}
            <div className="response-meta">
              <span>{response.mode === "openai" ? response.model : `${response.mode} mode`}</span>
              {response.citations[0]?.as_of && <span>Data {response.citations[0].as_of}</span>}
            </div>
          </div>
        )}
        {error && <div className="inline-error">{error}</div>}
      </div>
      <form className="copilot-form" onSubmit={ask}>
        <label htmlFor="copilot-question" className="sr-only">Ask Portfolio Copilot</label>
        <textarea
          id="copilot-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about this portfolio…"
          rows={2}
          maxLength={1000}
        />
        <button type="submit" disabled={loading || !question.trim()} aria-label="Send question">
          {loading ? <span className="spinner small" /> : <Icon name="arrow" />}
        </button>
      </form>
      <div className="copilot-foot">
        <Icon name="shield" size={13} />
        Analytics only · No investment advice
      </div>
    </section>
  );
}
