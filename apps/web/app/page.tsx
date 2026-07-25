"use client";

import { useEffect, useState } from "react";
import { DEMO_TOKEN } from "./api";
import { Dashboard } from "./components/Dashboard";
import { Icon } from "./components/Icons";

function Login({ onEnter }: { onEnter: () => void }) {
  return (
    <main className="login-page">
      <div className="login-decoration one" />
      <div className="login-decoration two" />
      <section className="login-story">
        <div className="brand login-brand">
          <img src="/mark.svg" alt="" />
          <div><strong>AssetLens</strong><span>RESEARCH WORKBENCH</span></div>
        </div>
        <div className="login-copy">
          <div className="eyebrow light">PORTFOLIO INTELLIGENCE, EXPLAINED</div>
          <h1>See the story<br />behind the numbers.</h1>
          <p>
            Analyze performance, understand risk, test market scenarios, and ask grounded
            questions—all from one reproducible research workspace.
          </p>
          <div className="feature-row">
            <div><Icon name="scenario" /><span><strong>Transparent analytics</strong><small>Formula, period, and timestamp on every metric</small></span></div>
            <div><Icon name="copilot" /><span><strong>Grounded copilot</strong><small>Read-only tools with citations and guardrails</small></span></div>
          </div>
        </div>
        <div className="login-disclaimer">Independent demonstration · Not affiliated with TD · Not investment advice</div>
      </section>
      <section className="login-panel">
        <div className="login-box">
          <div className="demo-chip"><i /> SEEDED DEMONSTRATION</div>
          <h2>Explore AssetLens</h2>
          <p>No account or market-data subscription required. Enter a read-only workspace with a complete Canadian portfolio.</p>
          <div className="demo-summary">
            <div className="demo-avatar">CG</div>
            <div><strong>Canadian Growth & Income</strong><span>8 holdings · S&amp;P/TSX benchmark</span></div>
            <Icon name="chevron" />
          </div>
          <button className="enter-button" onClick={onEnter}>
            Enter demo workspace <Icon name="arrow" />
          </button>
          <div className="secure-note"><Icon name="shield" size={15} /> Read-only demo · No personal financial data</div>
          <div className="login-rule"><span>WHAT YOU CAN EXPLORE</span></div>
          <ul className="login-list">
            <li><span>01</span>Portfolio performance and benchmark comparison</li>
            <li><span>02</span>Risk, exposure, and return attribution</li>
            <li><span>03</span>Deterministic scenario analysis</li>
            <li><span>04</span>Grounded research copilot and PDF export</li>
          </ul>
        </div>
      </section>
    </main>
  );
}

export default function Home() {
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);
  useEffect(() => setAuthenticated(localStorage.getItem("assetlens-token") === DEMO_TOKEN), []);
  if (authenticated === null) return <div className="boot-screen"><span className="spinner" /></div>;
  if (!authenticated) {
    return (
      <Login
        onEnter={() => {
          localStorage.setItem("assetlens-token", DEMO_TOKEN);
          setAuthenticated(true);
        }}
      />
    );
  }
  return (
    <Dashboard
      onSignOut={() => {
        localStorage.removeItem("assetlens-token");
        setAuthenticated(false);
      }}
    />
  );
}
