export type Portfolio = {
  id: string;
  name: string;
  benchmark: string;
  benchmark_name: string;
  archived: boolean;
};

export type Holding = {
  id: string;
  symbol: string;
  name: string;
  sector: string;
  asset_class: string;
  geography: string;
  currency: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_gain: number;
  unrealized_return: number;
  daily_change: number;
  weight: number;
};

export type Snapshot = {
  portfolio: Portfolio;
  holdings: Holding[];
  summary: {
    market_value: number;
    cost_basis: number;
    unrealized_gain: number;
    unrealized_return: number;
    realized_gain: number;
  };
  as_of: string;
  calculated_at: string;
  methodology: string;
};

export type PerformancePoint = {
  date: string;
  portfolio_value: number;
  portfolio_return: number;
  benchmark_return: number;
  drawdown: number;
};

export type Performance = {
  series: PerformancePoint[];
  metrics: {
    time_weighted_return: number;
    money_weighted_return: number;
    benchmark_return: number;
    active_return: number;
    annualized_volatility: number;
    sharpe_ratio: number;
    maximum_drawdown: number;
  };
  methodology: Record<string, { formula: string; period: string }>;
  as_of: string;
  calculated_at: string;
};

export type AllocationItem = { name: string; value: number; weight: number };

export type Exposure = {
  allocation: {
    sector: AllocationItem[];
    asset_class: AllocationItem[];
    geography: AllocationItem[];
    security: AllocationItem[];
  };
  concentration_warnings: string[];
  as_of: string;
  calculated_at: string;
};

export type Contributor = {
  symbol: string;
  name: string;
  sector: string;
  start_weight: number;
  holding_return: number;
  contribution: number;
};

export type Attribution = {
  contributors: Contributor[];
  top_positive: Contributor[];
  top_negative: Contributor[];
  as_of: string;
};

export type ScenarioDefinition = {
  type: string;
  label: string;
  description: string;
};

export type ScenarioResult = {
  portfolio_value: number;
  estimated_impact: number;
  estimated_impact_percent: number;
  estimated_post_scenario_value: number;
  affected_holdings: Array<{
    symbol: string;
    market_value: number;
    shock: number;
    estimated_impact: number;
    estimated_value: number;
  }>;
  assumptions: string[];
  as_of: string;
};

export type ScenarioRun = {
  id: string;
  name: string;
  scenario_type: string;
  status: string;
  result: ScenarioResult | null;
  error: string | null;
};

export type Security = {
  id: string;
  symbol: string;
  name: string;
  sector: string;
  asset_class: string;
  geography: string;
  latest_price: number;
};

export type WatchlistItem = {
  id: string;
  security_id: string;
  symbol: string;
  name: string;
};

export type PriceAlert = {
  id: string;
  symbol: string;
  direction: string;
  threshold: number;
  enabled: boolean;
};
