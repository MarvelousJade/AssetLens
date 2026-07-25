"use client";

import { ChangeEvent, useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, downloadReport } from "../api";
import type {
  Attribution,
  Exposure,
  Holding,
  Performance,
  Portfolio,
  PriceAlert,
  ScenarioDefinition,
  ScenarioRun,
  Security,
  Snapshot,
  WatchlistItem,
} from "../types";
import { AllocationDonut, AttributionBars, DrawdownChart, PerformanceChart } from "./Charts";
import { Copilot } from "./Copilot";
import { Icon } from "./Icons";

type Tab = "overview" | "holdings" | "scenarios" | "research";

const currency = new Intl.NumberFormat("en-CA", {
  style: "currency",
  currency: "CAD",
  maximumFractionDigits: 0,
});

function percentage(value: number, digits = 1) {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(digits)}%`;
}

function LoadingDashboard() {
  return (
    <div className="app-shell">
      <div className="loading-screen">
        <img src="/mark.svg" alt="" />
        <span className="spinner" />
        <p>Calculating portfolio analytics…</p>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
  tone = "neutral",
  formula,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "positive" | "negative" | "neutral";
  formula?: string;
}) {
  return (
    <div className="metric-card" title={formula}>
      <div className="metric-label">{label}{formula && <span className="info-dot">i</span>}</div>
      <strong className={tone === "positive" ? "positive-text" : tone === "negative" ? "negative-text" : ""}>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function HoldingsTable({ holdings }: { holdings: Holding[] }) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState<keyof Holding>("market_value");
  const [descending, setDescending] = useState(true);
  const filtered = useMemo(
    () =>
      holdings
        .filter((holding) =>
          `${holding.symbol} ${holding.name} ${holding.sector}`.toLowerCase().includes(search.toLowerCase()),
        )
        .sort((a, b) => {
          const left = a[sort];
          const right = b[sort];
          const compared =
            typeof left === "number" && typeof right === "number"
              ? left - right
              : String(left).localeCompare(String(right));
          return descending ? -compared : compared;
        }),
    [holdings, search, sort, descending],
  );
  function updateSort(next: keyof Holding) {
    if (next === sort) setDescending((value) => !value);
    else {
      setSort(next);
      setDescending(true);
    }
  }
  return (
    <>
      <div className="table-tools">
        <div className="search-box">
          <Icon name="research" size={16} />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter holdings" />
        </div>
        <span>{filtered.length} securities</span>
      </div>
      <div className="table-scroll">
        <table className="holdings-table">
          <thead>
            <tr>
              <th onClick={() => updateSort("symbol")}>Security</th>
              <th onClick={() => updateSort("sector")}>Sector</th>
              <th className="numeric" onClick={() => updateSort("quantity")}>Quantity</th>
              <th className="numeric" onClick={() => updateSort("current_price")}>Price</th>
              <th className="numeric" onClick={() => updateSort("market_value")}>Market value</th>
              <th className="numeric" onClick={() => updateSort("weight")}>Weight</th>
              <th className="numeric" onClick={() => updateSort("unrealized_return")}>Total return</th>
              <th className="numeric" onClick={() => updateSort("daily_change")}>Today</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((holding) => (
              <tr key={holding.id}>
                <td>
                  <div className="security-cell">
                    <span>{holding.symbol.slice(0, 2)}</span>
                    <div><strong>{holding.symbol}</strong><small>{holding.name}</small></div>
                  </div>
                </td>
                <td><span className="sector-tag">{holding.sector}</span></td>
                <td className="numeric">{holding.quantity.toLocaleString()}</td>
                <td className="numeric">{currency.format(holding.current_price)}</td>
                <td className="numeric"><strong>{currency.format(holding.market_value)}</strong></td>
                <td className="numeric">{(holding.weight * 100).toFixed(1)}%</td>
                <td className={`numeric ${holding.unrealized_return >= 0 ? "positive-text" : "negative-text"}`}>
                  {percentage(holding.unrealized_return)}
                </td>
                <td className={`numeric ${holding.daily_change >= 0 ? "positive-text" : "negative-text"}`}>
                  {percentage(holding.daily_change, 2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export function Dashboard({ onSignOut }: { onSignOut: () => void }) {
  const [tab, setTab] = useState<Tab>("overview");
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [portfolioId, setPortfolioId] = useState("demo-canadian-growth");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [performance, setPerformance] = useState<Performance | null>(null);
  const [exposure, setExposure] = useState<Exposure | null>(null);
  const [attribution, setAttribution] = useState<Attribution | null>(null);
  const [scenarioCatalog, setScenarioCatalog] = useState<ScenarioDefinition[]>([]);
  const [scenarioType, setScenarioType] = useState("technology_decline");
  const [scenarioRun, setScenarioRun] = useState<ScenarioRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reporting, setReporting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState("");
  const [importMessage, setImportMessage] = useState("");
  const [securities, setSecurities] = useState<Security[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [researchSearch, setResearchSearch] = useState("");

  const loadPortfolio = useCallback(async (selectedId: string, quiet = false) => {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError("");
    try {
      const [portfolioRows, nextSnapshot, nextPerformance, nextExposure, nextAttribution, scenarios] =
        await Promise.all([
          apiFetch<Portfolio[]>("/api/portfolios"),
          apiFetch<Snapshot>(`/api/portfolios/${selectedId}/holdings`),
          apiFetch<Performance>(`/api/portfolios/${selectedId}/performance`),
          apiFetch<Exposure>(`/api/portfolios/${selectedId}/exposure`),
          apiFetch<Attribution>(`/api/portfolios/${selectedId}/attribution`),
          apiFetch<ScenarioDefinition[]>("/api/scenarios/catalog"),
        ]);
      setPortfolios(portfolioRows);
      setSnapshot(nextSnapshot);
      setPerformance(nextPerformance);
      setExposure(nextExposure);
      setAttribution(nextAttribution);
      setScenarioCatalog(scenarios);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load portfolio analytics.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const loadResearch = useCallback(async () => {
    try {
      const query = researchSearch ? `?search=${encodeURIComponent(researchSearch)}` : "";
      const [securityRows, watchlistRows, alertRows] = await Promise.all([
        apiFetch<Security[]>(`/api/securities${query}`),
        apiFetch<WatchlistItem[]>("/api/watchlist"),
        apiFetch<PriceAlert[]>("/api/alerts"),
      ]);
      setSecurities(securityRows);
      setWatchlist(watchlistRows);
      setAlerts(alertRows);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load research data.");
    }
  }, [researchSearch]);

  useEffect(() => {
    void loadPortfolio(portfolioId);
  }, [loadPortfolio, portfolioId]);

  useEffect(() => {
    if (tab === "research") void loadResearch();
  }, [tab, loadResearch]);

  async function runScenario() {
    const definition = scenarioCatalog.find((item) => item.type === scenarioType);
    setError("");
    try {
      const created = await apiFetch<{ id: string }>(`/api/portfolios/${portfolioId}/scenarios`, {
        method: "POST",
        body: JSON.stringify({
          name: definition?.label ?? "Portfolio stress test",
          scenario_type: scenarioType,
          shocks: {},
        }),
      });
      for (let attempt = 0; attempt < 15; attempt += 1) {
        const run = await apiFetch<ScenarioRun>(`/api/scenario-runs/${created.id}`);
        setScenarioRun(run);
        if (["completed", "failed", "cancelled"].includes(run.status)) return;
        await new Promise((resolve) => window.setTimeout(resolve, 300));
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Scenario failed.");
    }
  }

  async function exportReport() {
    setReporting(true);
    setError("");
    try {
      const report = await apiFetch<{ id: string }>(`/api/portfolios/${portfolioId}/reports`, {
        method: "POST",
      });
      await downloadReport(report.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not export report.");
    } finally {
      setReporting(false);
    }
  }

  async function createPortfolio() {
    if (newPortfolioName.trim().length < 2) return;
    try {
      const created = await apiFetch<{ id: string }>("/api/portfolios", {
        method: "POST",
        body: JSON.stringify({ name: newPortfolioName.trim() }),
      });
      setNewPortfolioName("");
      setPortfolioId(created.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create portfolio.");
    }
  }

  async function importCsv(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setImportMessage("Validating import…");
    try {
      const result = await apiFetch<{ rows_imported: number }>(
        `/api/portfolios/${portfolioId}/imports`,
        { method: "POST", body: form },
      );
      setImportMessage(`${result.rows_imported} holdings imported atomically.`);
      await loadPortfolio(portfolioId, true);
    } catch (caught) {
      setImportMessage(caught instanceof Error ? caught.message : "Import failed.");
    } finally {
      event.target.value = "";
    }
  }

  async function addToWatchlist(security: Security) {
    await apiFetch(`/api/watchlist/${security.id}`, { method: "POST" });
    await loadResearch();
  }

  async function createPriceAlert(security: Security) {
    await apiFetch("/api/alerts", {
      method: "POST",
      body: JSON.stringify({
        symbol: security.symbol,
        direction: "above",
        threshold: Math.round((security.latest_price ?? 1) * 1.05 * 100) / 100,
      }),
    });
    await loadResearch();
  }

  if (loading) return <LoadingDashboard />;
  if (!snapshot || !performance || !exposure || !attribution) {
    return (
      <div className="fatal-state">
        <img src="/mark.svg" alt="" />
        <h1>Portfolio analytics unavailable</h1>
        <p>{error || "The portfolio does not have enough market data yet."}</p>
        <button className="primary-button" onClick={() => void loadPortfolio("demo-canadian-growth")}>Reload demo</button>
      </div>
    );
  }

  const metrics = performance.metrics;
  const currentPortfolio = portfolios.find((item) => item.id === portfolioId);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/mark.svg" alt="" />
          <div><strong>AssetLens</strong><span>RESEARCH WORKBENCH</span></div>
        </div>
        <nav aria-label="Primary navigation">
          {(["overview", "holdings", "scenarios", "research"] as Tab[]).map((item) => (
            <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>
              <Icon name={item === "scenarios" ? "scenario" : item} />
              <span>{item[0].toUpperCase() + item.slice(1)}</span>
              {item === "scenarios" && <i>LAB</i>}
            </button>
          ))}
        </nav>
        <div className="sidebar-callout">
          <Icon name="shield" />
          <strong>Research, grounded</strong>
          <p>Every calculation is reproducible and timestamped.</p>
        </div>
        <div className="user-card">
          <span>SF</span>
          <div><strong>Demo Analyst</strong><small>Read-only workspace</small></div>
          <button onClick={onSignOut} title="Sign out">×</button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="portfolio-select-wrap">
            <span className="portfolio-monogram">CG</span>
            <div>
              <label htmlFor="portfolio-select">PORTFOLIO</label>
              <select
                id="portfolio-select"
                value={portfolioId}
                onChange={(event) => setPortfolioId(event.target.value)}
              >
                {portfolios.filter((item) => !item.archived).map((item) => (
                  <option key={item.id} value={item.id}>{item.name}</option>
                ))}
              </select>
            </div>
            <Icon name="chevron" size={15} />
          </div>
          <div className="top-actions">
            <div className="data-freshness"><i /><span>Data through <strong>{snapshot.as_of}</strong></span></div>
            <button className="icon-button" onClick={() => void loadPortfolio(portfolioId, true)} title="Refresh">
              <span className={refreshing ? "rotating" : ""}><Icon name="refresh" /></span>
            </button>
            <button className="export-button" onClick={exportReport} disabled={reporting}>
              {reporting ? <span className="spinner small" /> : <Icon name="download" />}
              Export report
            </button>
          </div>
        </header>

        {error && <div className="global-error"><span>{error}</span><button onClick={() => setError("")}>×</button></div>}

        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">{tab === "overview" ? "PORTFOLIO OVERVIEW" : tab.toUpperCase()}</div>
              <h1>
                {tab === "overview" ? "Clarity behind every position." :
                  tab === "holdings" ? "Know what you own." :
                    tab === "scenarios" ? "Stress the assumptions." : "Extend your research."}
              </h1>
              <p>
                {tab === "overview" ? `Performance, risk, and attribution for ${currentPortfolio?.name}.` :
                  tab === "holdings" ? "Filter, compare, and import positions with atomic validation." :
                    tab === "scenarios" ? "Apply transparent, deterministic shocks to today's portfolio." :
                      "Screen the coverage universe and configure monitoring."}
              </p>
            </div>
            <div className="asof-chip"><Icon name="clock" size={15} /> Calculated {new Date(performance.calculated_at).toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" })}</div>
          </div>

          {tab === "overview" && (
            <div className="overview-grid">
              <section className="metric-strip">
                <MetricCard label="Portfolio value" value={currency.format(snapshot.summary.market_value)} detail={`${snapshot.holdings.length} positions · CAD`} />
                <MetricCard
                  label="Period return"
                  value={percentage(metrics.time_weighted_return)}
                  detail={`${currency.format(snapshot.summary.unrealized_gain)} unrealized`}
                  tone={metrics.time_weighted_return >= 0 ? "positive" : "negative"}
                  formula={performance.methodology.time_weighted_return.formula}
                />
                <MetricCard
                  label="Active return"
                  value={percentage(metrics.active_return)}
                  detail={`vs. ${snapshot.portfolio.benchmark_name}`}
                  tone={metrics.active_return >= 0 ? "positive" : "negative"}
                />
                <MetricCard
                  label="Maximum drawdown"
                  value={percentage(metrics.maximum_drawdown)}
                  detail={`${(metrics.annualized_volatility * 100).toFixed(1)}% annualized volatility`}
                  tone="negative"
                  formula={performance.methodology.maximum_drawdown.formula}
                />
              </section>

              <section className="card performance-card">
                <div className="card-head">
                  <div><div className="eyebrow">CUMULATIVE RETURN</div><h2>Performance vs. benchmark</h2></div>
                  <div className="chart-legend-inline"><span className="portfolio-key" />Portfolio <span className="benchmark-key" />Benchmark</div>
                </div>
                <PerformanceChart series={performance.series} />
                <div className="chart-summary">
                  <div><span>Portfolio</span><strong>{percentage(metrics.time_weighted_return)}</strong></div>
                  <div><span>Benchmark</span><strong>{percentage(metrics.benchmark_return)}</strong></div>
                  <div><span>Tracking difference</span><strong className={metrics.active_return >= 0 ? "positive-text" : "negative-text"}>{percentage(metrics.active_return)}</strong></div>
                </div>
              </section>

              <section className="card allocation-card">
                <div className="card-head">
                  <div><div className="eyebrow">CURRENT EXPOSURE</div><h2>Sector allocation</h2></div>
                </div>
                <AllocationDonut items={exposure.allocation.sector} />
                {exposure.concentration_warnings.length > 0 && (
                  <div className="warning-note"><Icon name="alert" size={16} />{exposure.concentration_warnings[0]}</div>
                )}
              </section>

              <section className="card attribution-card">
                <div className="card-head">
                  <div><div className="eyebrow">RETURN ATTRIBUTION</div><h2>Holding contribution</h2></div>
                  <span className="period-pill">Full period</span>
                </div>
                <AttributionBars items={attribution.contributors} />
              </section>

              <section className="card risk-card">
                <div className="card-head">
                  <div><div className="eyebrow">RISK PROFILE</div><h2>Drawdown & efficiency</h2></div>
                </div>
                <DrawdownChart series={performance.series} />
                <div className="risk-metrics">
                  <div><span>Sharpe ratio</span><strong>{metrics.sharpe_ratio.toFixed(2)}</strong><small>2% risk-free rate</small></div>
                  <div><span>Volatility</span><strong>{(metrics.annualized_volatility * 100).toFixed(1)}%</strong><small>Annualized</small></div>
                  <div><span>Max drawdown</span><strong className="negative-text">{(metrics.maximum_drawdown * 100).toFixed(1)}%</strong><small>Peak to trough</small></div>
                </div>
              </section>

              <Copilot portfolioId={portfolioId} />
            </div>
          )}

          {tab === "holdings" && (
            <div className="stack">
              <section className="card holdings-card">
                <div className="card-head">
                  <div><div className="eyebrow">POSITION DETAIL</div><h2>Current holdings</h2></div>
                  <span className="total-value">{currency.format(snapshot.summary.market_value)} total</span>
                </div>
                <HoldingsTable holdings={snapshot.holdings} />
              </section>
              <div className="two-column">
                <section className="card import-card">
                  <div className="icon-title"><span><Icon name="upload" /></span><div><h2>Import holdings CSV</h2><p>Validated as one transaction—invalid files change nothing.</p></div></div>
                  <label className="file-button">
                    Choose CSV file
                    <input type="file" accept=".csv,text/csv" onChange={importCsv} />
                  </label>
                  {importMessage && <div className="import-message">{importMessage}</div>}
                </section>
                <section className="card import-card">
                  <div className="icon-title"><span><Icon name="plus" /></span><div><h2>Create portfolio</h2><p>Start empty, then import a holdings file.</p></div></div>
                  <div className="create-row">
                    <input value={newPortfolioName} onChange={(event) => setNewPortfolioName(event.target.value)} placeholder="Portfolio name" />
                    <button onClick={createPortfolio} disabled={newPortfolioName.trim().length < 2}>Create</button>
                  </div>
                </section>
              </div>
            </div>
          )}

          {tab === "scenarios" && (
            <div className="scenario-layout">
              <section className="card scenario-builder">
                <div className="eyebrow">DETERMINISTIC STRESS LAB</div>
                <h2>Choose a market shock</h2>
                <p>Scenarios apply transparent percentage shocks to current values. They do not predict future prices.</p>
                <div className="scenario-options">
                  {scenarioCatalog.map((scenario) => (
                    <label key={scenario.type} className={scenarioType === scenario.type ? "selected" : ""}>
                      <input type="radio" name="scenario" value={scenario.type} checked={scenarioType === scenario.type} onChange={() => setScenarioType(scenario.type)} />
                      <span className="radio" />
                      <div><strong>{scenario.label}</strong><small>{scenario.description}</small></div>
                    </label>
                  ))}
                </div>
                <button className="run-button" onClick={runScenario}>
                  <Icon name="scenario" /> Run scenario
                </button>
              </section>
              <section className="card scenario-output">
                {!scenarioRun && (
                  <div className="empty-scenario">
                    <div><Icon name="scenario" size={30} /></div>
                    <h2>Ready to stress test</h2>
                    <p>Select a shock to estimate the portfolio impact and see which holdings are most affected.</p>
                  </div>
                )}
                {scenarioRun && scenarioRun.status !== "completed" && (
                  <div className="empty-scenario"><span className="spinner" /><h2>{scenarioRun.status}</h2><p>The job is running with safe retry semantics.</p></div>
                )}
                {scenarioRun?.result && (
                  <div className="scenario-results">
                    <div className="eyebrow">ESTIMATED IMPACT</div>
                    <div className="impact-number">{currency.format(scenarioRun.result.estimated_impact)}</div>
                    <div className="impact-percent">{percentage(scenarioRun.result.estimated_impact_percent)}</div>
                    <div className="value-bridge">
                      <div><span>Current value</span><strong>{currency.format(scenarioRun.result.portfolio_value)}</strong></div>
                      <span>→</span>
                      <div><span>Post-scenario</span><strong>{currency.format(scenarioRun.result.estimated_post_scenario_value)}</strong></div>
                    </div>
                    <h3>Most affected holdings</h3>
                    <div className="impact-list">
                      {scenarioRun.result.affected_holdings.slice(0, 5).map((holding) => (
                        <div key={holding.symbol}>
                          <strong>{holding.symbol}</strong>
                          <span>{percentage(holding.shock)}</span>
                          <b>{currency.format(holding.estimated_impact)}</b>
                        </div>
                      ))}
                    </div>
                    <details className="assumptions"><summary>Assumptions & limitations</summary><ul>{scenarioRun.result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></details>
                  </div>
                )}
              </section>
            </div>
          )}

          {tab === "research" && (
            <div className="research-layout">
              <section className="card screener-card">
                <div className="card-head">
                  <div><div className="eyebrow">SECURITY SCREENER</div><h2>Coverage universe</h2></div>
                  <div className="search-box"><Icon name="research" size={16} /><input value={researchSearch} onChange={(event) => setResearchSearch(event.target.value)} placeholder="Ticker or name" /></div>
                </div>
                <div className="security-list">
                  {securities.map((security) => {
                    const watched = watchlist.some((item) => item.security_id === security.id);
                    return (
                      <div key={security.id}>
                        <span className="ticker-box">{security.symbol.slice(0, 2)}</span>
                        <div className="security-info"><strong>{security.symbol} <small>{security.name}</small></strong><span>{security.sector} · {security.geography}</span></div>
                        <b>{currency.format(security.latest_price)}</b>
                        <button disabled={watched} onClick={() => void addToWatchlist(security)}><Icon name="eye" size={16} />{watched ? "Watching" : "Watch"}</button>
                        <button onClick={() => void createPriceAlert(security)}><Icon name="alert" size={16} />Alert</button>
                      </div>
                    );
                  })}
                </div>
              </section>
              <div className="research-side">
                <section className="card compact-card">
                  <div className="card-head"><div><div className="eyebrow">WATCHLIST</div><h2>Monitoring</h2></div><span>{watchlist.length}</span></div>
                  {watchlist.length ? watchlist.map((item) => <div className="watch-row" key={item.id}><strong>{item.symbol}</strong><span>{item.name}</span><i /></div>) : <p className="empty-copy">Add securities from the screener.</p>}
                </section>
                <section className="card compact-card">
                  <div className="card-head"><div><div className="eyebrow">PRICE ALERTS</div><h2>Configured</h2></div><span>{alerts.length}</span></div>
                  {alerts.length ? alerts.map((alert) => <div className="watch-row" key={alert.id}><strong>{alert.symbol}</strong><span>{alert.direction} {currency.format(alert.threshold)}</span><i /></div>) : <p className="empty-copy">Create a 5% upside alert from the screener.</p>}
                </section>
              </div>
            </div>
          )}
        </div>
        <footer>
          <span>AssetLens is an independent software demonstration. Not affiliated with TD.</span>
          <span>Educational research only · Not investment advice</span>
        </footer>
      </main>
    </div>
  );
}
