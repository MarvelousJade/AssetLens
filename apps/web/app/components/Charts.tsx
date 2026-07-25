import type { AllocationItem, Contributor, PerformancePoint } from "../types";

const colours = ["#123c3a", "#d8a84e", "#5e8c86", "#cc7058", "#7893ad", "#8c6f9d", "#a7a273"];

function linePath(values: number[], width: number, height: number, min: number, max: number) {
  const range = max - min || 1;
  return values
    .map((value, index) => {
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export function PerformanceChart({ series }: { series: PerformancePoint[] }) {
  const width = 760;
  const height = 250;
  const portfolio = series.map((item) => item.portfolio_return);
  const benchmark = series.map((item) => item.benchmark_return);
  const all = [...portfolio, ...benchmark];
  const min = Math.min(...all, -0.02);
  const max = Math.max(...all, 0.02);
  const portfolioPath = linePath(portfolio, width, height, min, max);
  const benchmarkPath = linePath(benchmark, width, height, min, max);
  const zeroY = height - ((0 - min) / (max - min || 1)) * height;
  const first = series.at(0)?.date;
  const middle = series.at(Math.floor(series.length / 2))?.date;
  const last = series.at(-1)?.date;

  return (
    <div className="chart-wrap" aria-label="Portfolio and benchmark cumulative return chart">
      <svg viewBox={`-10 -12 ${width + 28} ${height + 48}`} role="img">
        <defs>
          <linearGradient id="portfolio-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2d716b" stopOpacity=".24" />
            <stop offset="100%" stopColor="#2d716b" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <line
            key={fraction}
            x1="0"
            x2={width}
            y1={height * fraction}
            y2={height * fraction}
            className="chart-grid"
          />
        ))}
        <line x1="0" x2={width} y1={zeroY} y2={zeroY} className="chart-zero" />
        <path d={`${portfolioPath} L${width},${height} L0,${height} Z`} fill="url(#portfolio-fill)" />
        <path d={benchmarkPath} className="benchmark-line" />
        <path d={portfolioPath} className="portfolio-line" />
        <circle
          cx={width}
          cy={height - ((portfolio.at(-1)! - min) / (max - min || 1)) * height}
          r="4.5"
          className="chart-end"
        />
        <text x="0" y={height + 25} className="axis-label">{first}</text>
        <text x={width / 2} y={height + 25} textAnchor="middle" className="axis-label">{middle}</text>
        <text x={width} y={height + 25} textAnchor="end" className="axis-label">{last}</text>
      </svg>
    </div>
  );
}

export function DrawdownChart({ series }: { series: PerformancePoint[] }) {
  const width = 680;
  const height = 100;
  const values = series.map((item) => item.drawdown);
  const min = Math.min(...values, -0.01);
  const path = linePath(values, width, height, min, 0);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="drawdown-chart" aria-label="Portfolio drawdown chart">
      <defs>
        <linearGradient id="drawdown-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#cc7058" stopOpacity=".08" />
          <stop offset="100%" stopColor="#cc7058" stopOpacity=".4" />
        </linearGradient>
      </defs>
      <path d={`${path} L${width},0 L0,0 Z`} fill="url(#drawdown-fill)" />
      <path d={path} className="drawdown-line" />
    </svg>
  );
}

export function AllocationDonut({ items }: { items: AllocationItem[] }) {
  let cursor = 0;
  const stops = items.map((item, index) => {
    const start = cursor;
    cursor += item.weight * 100;
    return `${colours[index % colours.length]} ${start}% ${cursor}%`;
  });
  return (
    <div className="allocation-layout">
      <div className="donut" style={{ background: `conic-gradient(${stops.join(",")})` }}>
        <div className="donut-hole">
          <span>{items.length}</span>
          <small>sectors</small>
        </div>
      </div>
      <div className="legend">
        {items.map((item, index) => (
          <div className="legend-row" key={item.name}>
            <span className="legend-dot" style={{ background: colours[index % colours.length] }} />
            <span>{item.name}</span>
            <strong>{(item.weight * 100).toFixed(1)}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AttributionBars({ items }: { items: Contributor[] }) {
  const max = Math.max(...items.map((item) => Math.abs(item.contribution)), 0.01);
  return (
    <div className="attribution-bars">
      {items.map((item) => (
        <div className="attribution-row" key={item.symbol}>
          <strong>{item.symbol}</strong>
          <div className="bar-track">
            <div
              className={item.contribution >= 0 ? "bar positive" : "bar negative"}
              style={{ width: `${(Math.abs(item.contribution) / max) * 100}%` }}
            />
          </div>
          <span className={item.contribution >= 0 ? "positive-text" : "negative-text"}>
            {item.contribution >= 0 ? "+" : ""}
            {(item.contribution * 100).toFixed(2)}%
          </span>
        </div>
      ))}
    </div>
  );
}
