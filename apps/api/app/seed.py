import math
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import BenchmarkPrice, Holding, MarketPrice, Portfolio, Security

SECURITIES = [
    (
        "RY",
        "Royal Bank of Canada",
        "Financials",
        "Equity",
        "Canada",
        "CAD",
        45,
        126.10,
        151.20,
        0.00042,
        0.012,
    ),
    (
        "TD",
        "Toronto-Dominion Bank",
        "Financials",
        "Equity",
        "Canada",
        "CAD",
        52,
        81.30,
        79.85,
        -0.00005,
        0.014,
    ),
    ("SHOP", "Shopify", "Technology", "Equity", "Canada", "CAD", 28, 91.40, 118.30, 0.00085, 0.027),
    (
        "CSU",
        "Constellation Software",
        "Technology",
        "Equity",
        "Canada",
        "CAD",
        2,
        3680.00,
        4415.00,
        0.00055,
        0.016,
    ),
    (
        "CNR",
        "Canadian National Railway",
        "Industrials",
        "Equity",
        "Canada",
        "CAD",
        42,
        158.20,
        147.40,
        -0.00012,
        0.012,
    ),
    ("ENB", "Enbridge", "Energy", "Equity", "Canada", "CAD", 95, 49.10, 63.20, 0.00048, 0.010),
    (
        "XBB",
        "iShares Core Canadian Universe Bond ETF",
        "Fixed Income",
        "Fixed Income",
        "Canada",
        "CAD",
        180,
        29.15,
        28.65,
        0.00002,
        0.003,
    ),
    (
        "VFV",
        "Vanguard S&P 500 Index ETF",
        "Broad Market",
        "Equity",
        "United States",
        "CAD",
        62,
        121.20,
        151.85,
        0.00062,
        0.011,
    ),
]


def _business_days(end: date, count: int) -> list[date]:
    result: list[date] = []
    current = end
    while len(result) < count:
        if current.weekday() < 5:
            result.append(current)
        current -= timedelta(days=1)
    return list(reversed(result))


def _series(final_price: float, drift: float, amplitude: float, count: int, phase: float) -> list[float]:
    factors = []
    value = 1.0
    for index in range(count):
        market_cycle = math.sin(index * 2.17) * amplitude * 0.55
        long_cycle = math.cos(index * 0.73) * amplitude * 0.35
        idiosyncratic = math.sin((index + phase) * 1.37) * amplitude * 0.35
        event_return = 0.0
        if index == 170:
            event_return = -min(0.08, amplitude * 4)
        elif index == 171:
            event_return = -min(0.04, amplitude * 2)
        elif index == 190:
            event_return = min(0.06, amplitude * 3)
        elif index == 205:
            event_return = min(0.04, amplitude * 2)
        value *= 1 + drift + market_cycle + long_cycle + idiosyncratic + event_return
        factors.append(value)
    scale = final_price / factors[-1]
    return [round(item * scale, 4) for item in factors]


def seed_demo(db: Session) -> None:
    portfolio_count = db.scalar(select(func.count()).select_from(Portfolio))
    if portfolio_count:
        return

    portfolio = Portfolio(
        id="demo-canadian-growth",
        name="Canadian Growth & Income",
        benchmark="^GSPTSE",
        benchmark_name="S&P/TSX Composite",
    )
    db.add(portfolio)
    days = _business_days(date(2026, 7, 23), 260)

    for index, row in enumerate(SECURITIES):
        (
            symbol,
            name,
            sector,
            asset_class,
            geography,
            currency,
            quantity,
            cost,
            current,
            drift,
            vol,
        ) = row
        security = Security(
            symbol=symbol,
            name=name,
            sector=sector,
            asset_class=asset_class,
            geography=geography,
            currency=currency,
        )
        db.add(security)
        db.flush()
        db.add(
            Holding(
                portfolio_id=portfolio.id,
                security_id=security.id,
                quantity=quantity,
                average_cost=cost,
                acquired_at=date(2025, 7, 2),
            )
        )
        prices = _series(current, drift, vol, len(days), index * 7.0)
        db.add_all(
            [
                MarketPrice(security_id=security.id, price_date=day, close=price)
                for day, price in zip(days, prices, strict=True)
            ]
        )

    benchmark = _series(32750.0, 0.00050, 0.009, len(days), 4.0)
    db.add_all(
        [
            BenchmarkPrice(symbol="^GSPTSE", price_date=day, close=price)
            for day, price in zip(days, benchmark, strict=True)
        ]
    )
    db.commit()
