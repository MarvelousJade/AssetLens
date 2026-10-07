import math
import statistics
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import BenchmarkPrice, Holding, MarketPrice, Portfolio, Security


def _utc_iso() -> str:
    return datetime.now(UTC).isoformat()


def get_portfolio(db: Session, portfolio_id: str, owner_id: str) -> Portfolio:
    portfolio = db.scalar(
        select(Portfolio).where(Portfolio.id == portfolio_id, Portfolio.owner_id == owner_id)
    )
    if portfolio is None:
        raise LookupError("Portfolio not found")
    return portfolio


def _holding_rows(
    db: Session, portfolio_id: str, owner_id: str
) -> list[tuple[Holding, Security]]:
    return list(
        db.execute(
            select(Holding, Security)
            .join(Security, Holding.security_id == Security.id)
            .join(Portfolio, Holding.portfolio_id == Portfolio.id)
            .where(
                Holding.portfolio_id == portfolio_id,
                Portfolio.owner_id == owner_id,
            )
            .order_by(Security.symbol)
        ).all()
    )


def _price_map(db: Session, security_ids: list[str]) -> tuple[dict[str, dict[date, float]], list[date]]:
    if not security_ids:
        return {}, []
    rows = db.execute(
        select(MarketPrice).where(MarketPrice.security_id.in_(security_ids)).order_by(MarketPrice.price_date)
    ).scalars()
    result: dict[str, dict[date, float]] = defaultdict(dict)
    dates: set[date] = set()
    for row in rows:
        result[row.security_id][row.price_date] = row.close
        dates.add(row.price_date)
    return dict(result), sorted(dates)


def holdings_snapshot(db: Session, portfolio_id: str, owner_id: str) -> dict[str, Any]:
    portfolio = get_portfolio(db, portfolio_id, owner_id)
    rows = _holding_rows(db, portfolio_id, owner_id)
    prices, all_dates = _price_map(db, [holding.security_id for holding, _ in rows])
    as_of = all_dates[-1] if all_dates else date.today()
    values: list[dict[str, Any]] = []
    total_value = 0.0
    total_cost = 0.0

    for holding, security in rows:
        security_prices = prices.get(security.id, {})
        ordered = sorted(security_prices.items())
        current_price = ordered[-1][1] if ordered else holding.average_cost
        previous_price = ordered[-2][1] if len(ordered) > 1 else current_price
        market_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_cost
        total_value += market_value
        total_cost += cost_basis
        values.append(
            {
                "id": holding.id,
                "symbol": security.symbol,
                "name": security.name,
                "sector": security.sector,
                "asset_class": security.asset_class,
                "geography": security.geography,
                "currency": security.currency,
                "quantity": holding.quantity,
                "average_cost": round(holding.average_cost, 2),
                "current_price": round(current_price, 2),
                "market_value": round(market_value, 2),
                "cost_basis": round(cost_basis, 2),
                "unrealized_gain": round(market_value - cost_basis, 2),
                "unrealized_return": round((current_price / holding.average_cost) - 1, 6),
                "daily_change": round((current_price / previous_price) - 1, 6) if previous_price else 0.0,
            }
        )

    for item in values:
        item["weight"] = round(item["market_value"] / total_value, 6) if total_value else 0.0

    return {
        "portfolio": {
            "id": portfolio.id,
            "name": portfolio.name,
            "benchmark": portfolio.benchmark,
            "benchmark_name": portfolio.benchmark_name,
            "archived": portfolio.archived,
        },
        "holdings": values,
        "summary": {
            "market_value": round(total_value, 2),
            "cost_basis": round(total_cost, 2),
            "unrealized_gain": round(total_value - total_cost, 2),
            "unrealized_return": round(total_value / total_cost - 1, 6) if total_cost else 0.0,
            "realized_gain": 0.0,
        },
        "as_of": as_of.isoformat(),
        "calculated_at": _utc_iso(),
        "methodology": "Latest available close multiplied by current quantity; CAD display currency.",
    }


def _drawdown(values: list[float]) -> tuple[list[float], float]:
    peak = values[0] if values else 0.0
    result: list[float] = []
    minimum = 0.0
    for value in values:
        peak = max(values[0], value)
        drawdown = value / peak - 1 if peak else 0.0
        result.append(drawdown)
        minimum = min(minimum, drawdown)
    return result, minimum


def performance_analytics(
    db: Session, portfolio_id: str, owner_id: str
) -> dict[str, Any]:
    portfolio = get_portfolio(db, portfolio_id, owner_id)
    rows = _holding_rows(db, portfolio_id, owner_id)
    prices, all_dates = _price_map(db, [holding.security_id for holding, _ in rows])
    if not all_dates:
        raise ValueError("Portfolio has no market prices")

    latest_by_security = {
        security_id: sorted(series.items())[-1][1] for security_id, series in prices.items()
    }
    last_seen = {security_id: next(iter(sorted(series.items())))[1] for security_id, series in prices.items()}
    portfolio_values: list[float] = []
    for current_date in all_dates:
        total = 0.0
        for holding, security in rows:
            price = prices.get(security.id, {}).get(current_date)
            if price is not None:
                last_seen[security.id] = price
            total += holding.quantity * last_seen.get(
                security.id, latest_by_security.get(security.id, holding.average_cost)
            )
        portfolio_values.append(total)

    benchmark_rows = list(
        db.scalars(
            select(BenchmarkPrice)
            .where(
                BenchmarkPrice.symbol == portfolio.benchmark,
                BenchmarkPrice.price_date >= all_dates[0],
                BenchmarkPrice.price_date <= all_dates[-1],
            )
            .order_by(BenchmarkPrice.price_date)
        )
    )
    benchmark_by_date = {row.price_date: row.close for row in benchmark_rows}
    benchmark_values: list[float] = []
    benchmark_last = benchmark_rows[0].close if benchmark_rows else 1.0
    for current_date in all_dates:
        benchmark_last = benchmark_by_date.get(current_date, benchmark_last)
        benchmark_values.append(benchmark_last)

    daily_returns = [
        portfolio_values[index] / portfolio_values[index - 1] - 1
        for index in range(1, len(portfolio_values))
        if portfolio_values[index - 1]
    ]
    cumulative = [value / portfolio_values[0] - 1 for value in portfolio_values]
    benchmark_cumulative = [value / benchmark_values[0] - 1 for value in benchmark_values]
    drawdowns, max_drawdown = _drawdown(portfolio_values)
    volatility = statistics.stdev(daily_returns) * math.sqrt(252) if len(daily_returns) > 1 else 0.0
    annual_return = statistics.mean(daily_returns) * 252 if daily_returns else 0.0
    risk_free_rate = 0.02
    sharpe = (annual_return - risk_free_rate) / volatility if volatility else 0.0
    period_return = cumulative[-1]
    years = max((all_dates[-1] - all_dates[0]).days / 365.25, 1 / 365.25)
    money_weighted = (portfolio_values[-1] / portfolio_values[0]) ** (1 / years) - 1

    series = [
        {
            "date": current_date.isoformat(),
            "portfolio_value": round(portfolio_values[index], 2),
            "portfolio_return": round(cumulative[index], 6),
            "benchmark_return": round(benchmark_cumulative[index], 6),
            "drawdown": round(drawdowns[index], 6),
        }
        for index, current_date in enumerate(all_dates)
    ]
    period = f"{all_dates[0].isoformat()} to {all_dates[-1].isoformat()}"
    return {
        "series": series,
        "metrics": {
            "time_weighted_return": round(period_return, 6),
            "money_weighted_return": round(money_weighted, 6),
            "benchmark_return": round(benchmark_cumulative[-1], 6),
            "active_return": round(period_return - benchmark_cumulative[-1], 6),
            "annualized_volatility": round(volatility, 6),
            "sharpe_ratio": round(sharpe, 4),
            "maximum_drawdown": round(max_drawdown, 6),
        },
        "methodology": {
            "time_weighted_return": {
                "formula": "Ending unit value / beginning unit value - 1",
                "period": period,
            },
            "money_weighted_return": {
                "formula": "(ending value / beginning value)^(1 / years) - 1; no interim cash flows",
                "period": period,
            },
            "annualized_volatility": {
                "formula": "Sample standard deviation of daily returns × √252",
                "period": period,
            },
            "sharpe_ratio": {
                "formula": "(annualized arithmetic return - 2% risk-free rate) / volatility",
                "period": period,
            },
            "maximum_drawdown": {
                "formula": "Minimum(value / running peak - 1)",
                "period": period,
            },
        },
        "as_of": all_dates[-1].isoformat(),
        "calculated_at": _utc_iso(),
    }


def exposure_analytics(db: Session, portfolio_id: str, owner_id: str) -> dict[str, Any]:
    snapshot = holdings_snapshot(db, portfolio_id, owner_id)
    buckets: dict[str, dict[str, float]] = {
        "sector": defaultdict(float),
        "asset_class": defaultdict(float),
        "geography": defaultdict(float),
        "security": defaultdict(float),
    }
    for holding in snapshot["holdings"]:
        value = holding["market_value"]
        buckets["sector"][holding["sector"]] += value
        buckets["asset_class"][holding["asset_class"]] += value
        buckets["geography"][holding["geography"]] += value
        buckets["security"][holding["symbol"]] += value
    total = snapshot["summary"]["market_value"]

    def normalized(values: dict[str, float]) -> list[dict[str, Any]]:
        return sorted(
            [
                {"name": key, "value": round(value, 2), "weight": round(value / total, 6)}
                for key, value in values.items()
            ],
            key=lambda item: item["weight"],
            reverse=True,
        )

    allocation = {name: normalized(dict(values)) for name, values in buckets.items()}
    warnings: list[str] = []
    for item in allocation["security"]:
        if item["weight"] >= 0.2:
            warnings.append(f"{item['name']} represents {item['weight']:.1%} of portfolio value.")
    for item in allocation["sector"]:
        if item["weight"] >= 0.35:
            warnings.append(f"{item['name']} represents {item['weight']:.1%} of portfolio value.")
    return {
        "allocation": allocation,
        "concentration_warnings": warnings,
        "as_of": snapshot["as_of"],
        "calculated_at": _utc_iso(),
        "methodology": "Latest market value grouped by security metadata.",
    }


def attribution_analytics(
    db: Session, portfolio_id: str, owner_id: str
) -> dict[str, Any]:
    get_portfolio(db, portfolio_id, owner_id)
    rows = _holding_rows(db, portfolio_id, owner_id)
    prices, all_dates = _price_map(db, [holding.security_id for holding, _ in rows])
    if not all_dates:
        return {"contributors": [], "as_of": date.today().isoformat(), "calculated_at": _utc_iso()}
    start_values: dict[str, float] = {}
    end_values: dict[str, float] = {}
    total_start = 0.0
    for holding, security in rows:
        ordered = sorted(prices.get(security.id, {}).items())
        start_price = ordered[0][1] if ordered else holding.average_cost
        end_price = ordered[-1][1] if ordered else holding.average_cost
        start_values[security.id] = start_price * holding.quantity
        end_values[security.id] = end_price * holding.quantity
        total_start += start_values[security.id]
    contributors = []
    for _holding, security in rows:
        start_value = start_values[security.id]
        end_value = end_values[security.id]
        holding_return = end_value / start_value - 1 if start_value else 0.0
        contribution = (end_value - start_value) / total_start if total_start else 0.0
        contributors.append(
            {
                "symbol": security.symbol,
                "name": security.name,
                "sector": security.sector,
                "start_weight": round(start_value / total_start, 6) if total_start else 0.0,
                "holding_return": round(holding_return, 6),
                "contribution": round(contribution, 6),
            }
        )
    contributors.sort(key=lambda item: item["contribution"], reverse=True)
    return {
        "contributors": contributors,
        "top_positive": contributors[:3],
        "top_negative": list(reversed(contributors[-3:])),
        "as_of": all_dates[-1].isoformat(),
        "calculated_at": _utc_iso(),
        "methodology": "Beginning weight × holding total return; no trading effects in seeded period.",
    }
