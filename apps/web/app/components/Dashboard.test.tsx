import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../api";
import type { Portfolio, Snapshot } from "../types";
import { Dashboard } from "./Dashboard";

vi.mock("../api", () => ({ apiFetch: vi.fn(), downloadReport: vi.fn() }));
vi.mock("./Charts", () => ({
  AllocationDonut: () => null,
  AttributionBars: () => null,
  DrawdownChart: () => null,
  PerformanceChart: () => null,
}));
vi.mock("./Copilot", () => ({ Copilot: () => null }));

const demo: Portfolio = {
  id: "demo-canadian-growth", name: "Seeded portfolio", benchmark: "^GSPTSE",
  benchmark_name: "Demo benchmark", archived: false,
};
const empty: Portfolio = { ...demo, id: "new-portfolio", name: "New portfolio" };
const unavailable: Portfolio = { ...demo, id: "unavailable-portfolio", name: "Unavailable analytics" };

function snapshot(portfolio: Portfolio, symbol?: string): Snapshot {
  return {
    portfolio,
    holdings: symbol ? [{
      id: symbol, symbol, name: `${symbol} holding`, sector: "Technology", asset_class: "Equity",
      geography: "Canada", currency: "CAD", quantity: 2, average_cost: 10, current_price: 12,
      market_value: 24, cost_basis: 20, unrealized_gain: 4, unrealized_return: 0.2,
      daily_change: 0, weight: 1,
    }] : [],
    summary: { market_value: symbol ? 24 : 0, cost_basis: symbol ? 20 : 0,
      unrealized_gain: symbol ? 4 : 0, unrealized_return: symbol ? 0.2 : 0, realized_gain: 0 },
    as_of: "2026-01-02", calculated_at: "2026-01-02T12:00:00Z", methodology: "Test fixture",
  };
}

const performance = {
  series: [], as_of: "2026-01-02", calculated_at: "2026-01-02T12:00:00Z",
  metrics: { time_weighted_return: 0, money_weighted_return: 0, benchmark_return: 0,
    active_return: 0, annualized_volatility: 0, sharpe_ratio: 0, maximum_drawdown: 0 },
  methodology: { time_weighted_return: { formula: "Test", period: "Test" },
    maximum_drawdown: { formula: "Test", period: "Test" } },
};

let created: boolean;
let imported: boolean;

beforeEach(() => {
  created = false;
  imported = false;
  vi.mocked(apiFetch).mockReset();
  vi.mocked(apiFetch).mockImplementation(async (path, options) => {
    if (path === "/api/portfolios" && options?.method === "POST") {
      created = true;
      return { id: empty.id };
    }
    if (path === "/api/portfolios") return created ? [demo, empty, unavailable] : [demo, unavailable];
    if (path === "/api/scenarios/catalog") return [];
    if (path === `/api/portfolios/${empty.id}/imports`) {
      expect(options?.body).toBeInstanceOf(FormData);
      imported = true;
      return { rows_imported: 1 };
    }
    const portfolio = path.includes(unavailable.id) ? unavailable : path.includes(empty.id) ? empty : demo;
    if (path.endsWith("/holdings")) {
      return snapshot(portfolio, portfolio === empty ? imported ? "IMPORTED" : undefined :
        portfolio === unavailable ? "CURRENT" : "SEEDED");
    }
    if (portfolio === empty && !imported) throw new Error("Portfolio has no market prices");
    if (portfolio === unavailable) throw new Error("Analytics service unavailable");
    if (path.endsWith("/performance")) return performance;
    if (path.endsWith("/exposure")) return {
      allocation: { sector: [], asset_class: [], geography: [], security: [] }, concentration_warnings: [],
    };
    if (path.endsWith("/attribution")) return { contributors: [], top_positive: [], top_negative: [] };
    throw new Error(`Unexpected request: ${path}`);
  });
});
afterEach(cleanup);

describe("Portfolio loading", () => {
  it("ignores an older refresh after selecting a different portfolio", async () => {
    created = true;
    const original = vi.mocked(apiFetch).getMockImplementation()!;
    let delayRefresh = false;
    let releaseRefresh!: (value: Snapshot) => void;
    const oldSnapshot = new Promise<Snapshot>((resolve) => { releaseRefresh = resolve; });
    vi.mocked(apiFetch).mockImplementation((path, options, token) => {
      if (delayRefresh && path === `/api/portfolios/${demo.id}/holdings`) {
        delayRefresh = false;
        return oldSnapshot;
      }
      return original(path, options, token);
    });
    render(<Dashboard onSignOut={vi.fn()} />);
    await screen.findByRole("heading", { name: "Clarity behind every position." });
    fireEvent.click(screen.getByRole("button", { name: "Holdings" }));
    delayRefresh = true;
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    fireEvent.change(screen.getByRole("combobox", { name: "PORTFOLIO" }), {
      target: { value: empty.id },
    });
    await screen.findByText("No holdings yet. Import a CSV to get started.");
    await act(async () => { releaseRefresh(snapshot(demo, "SEEDED")); });
    expect(screen.queryByText("SEEDED")).not.toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "PORTFOLIO" })).toHaveValue(empty.id);
    expect(screen.getByRole("button", { name: "Export report" })).toBeDisabled();
  });

  it("creates an empty portfolio, keeps import usable, and loads imported analytics", async () => {
    render(<Dashboard onSignOut={vi.fn()} />);
    await screen.findByRole("heading", { name: "Clarity behind every position." });
    fireEvent.click(screen.getByRole("button", { name: "Holdings" }));
    expect(screen.getByText("SEEDED")).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText("Portfolio name"), { target: { value: empty.name } });
    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "PORTFOLIO" })).toHaveValue(empty.id));
    expect(screen.queryByText("SEEDED")).not.toBeInTheDocument();
    expect(screen.getByText("No holdings yet. Import a CSV to get started.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export report" })).toBeDisabled();
    expect(vi.mocked(apiFetch).mock.calls.some(([path]) => path === `/api/portfolios/${empty.id}/performance`))
      .toBe(false);
    fireEvent.change(screen.getByLabelText("Choose CSV file"), {
      target: { files: [new File(["ticker,quantity,average_cost\nIMPORTED,2,10\n"], "holdings.csv")] },
    });
    await screen.findByText("IMPORTED");
    expect(screen.getByRole("button", { name: "Export report" })).toBeEnabled();
    expect(screen.getByText("1 holdings imported atomically.")).toBeInTheDocument();
  });

  it("retains only the selected holdings when that portfolio's analytics fail", async () => {
    render(<Dashboard onSignOut={vi.fn()} />);
    await screen.findByRole("heading", { name: "Clarity behind every position." });
    fireEvent.click(screen.getByRole("button", { name: "Holdings" }));
    fireEvent.change(screen.getByRole("combobox", { name: "PORTFOLIO" }), {
      target: { value: unavailable.id },
    });
    await screen.findByText("Analytics service unavailable");
    expect(screen.queryByText("SEEDED")).not.toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "PORTFOLIO" })).toHaveValue(unavailable.id);
    expect(screen.getByRole("button", { name: "Export report" })).toBeDisabled();
  });
});
