from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    benchmark: Mapped[str] = mapped_column(String(30), default="^GSPTSE")
    benchmark_name: Mapped[str] = mapped_column(String(120), default="S&P/TSX Composite")
    owner_id: Mapped[str] = mapped_column(String(60), default="demo-user")
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    holdings: Mapped[list["Holding"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class Security(Base):
    __tablename__ = "securities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    sector: Mapped[str] = mapped_column(String(80))
    asset_class: Mapped[str] = mapped_column(String(80), default="Equity")
    geography: Mapped[str] = mapped_column(String(80), default="Canada")
    currency: Mapped[str] = mapped_column(String(3), default="CAD")
    holdings: Mapped[list["Holding"]] = relationship(back_populates="security")
    prices: Mapped[list["MarketPrice"]] = relationship(
        back_populates="security", cascade="all, delete-orphan"
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float)
    average_cost: Mapped[float] = mapped_column(Float)
    acquired_at: Mapped[date] = mapped_column(Date, default=date(2025, 1, 2))
    portfolio: Mapped[Portfolio] = relationship(back_populates="holdings")
    security: Mapped[Security] = relationship(back_populates="holdings")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    price_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[float] = mapped_column(Float)
    security: Mapped[Security] = relationship(back_populates="prices")


class BenchmarkPrice(Base):
    __tablename__ = "benchmark_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    symbol: Mapped[str] = mapped_column(String(30), index=True)
    price_date: Mapped[date] = mapped_column(Date, index=True)
    close: Mapped[float] = mapped_column(Float)


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    scenario_type: Mapped[str] = mapped_column(String(60))
    shocks: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportRecord(Base):
    __tablename__ = "import_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    rows_imported: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CopilotToolCall(Base):
    __tablename__ = "copilot_tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str] = mapped_column(String(80))
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    source_id: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(String(60), default="demo-user", index=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(String(60), default="demo-user", index=True)
    security_id: Mapped[str] = mapped_column(ForeignKey("securities.id"), index=True)
    direction: Mapped[str] = mapped_column(String(10))
    threshold: Mapped[float] = mapped_column(Float)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    actor_id: Mapped[str] = mapped_column(String(60), default="demo-user")
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(60))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
