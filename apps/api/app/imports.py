import csv
import hashlib
import io
import math
import re
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .analytics import get_portfolio
from .models import AuditEvent, Holding, ImportRecord, MarketPrice, Security

TICKER_PATTERN = re.compile(r"^[A-Z][A-Z0-9.^-]{0,14}$")
REQUIRED_COLUMNS = {"ticker", "quantity", "average_cost"}


def _number(row: dict[str, str], key: str, row_number: int, errors: list[dict[str, Any]]) -> float:
    try:
        value = float((row.get(key) or "").strip())
        if not math.isfinite(value) or value <= 0:
            raise ValueError
        return value
    except ValueError:
        errors.append({"row": row_number, "field": key, "message": "Must be a finite positive number."})
        return 0.0


def import_holdings_csv(
    db: Session, portfolio_id: str, owner_id: str, content: bytes
) -> dict[str, Any]:
    get_portfolio(db, portfolio_id, owner_id)
    if len(content) > 1_000_000:
        raise ValueError("CSV must be smaller than 1 MB.")
    content_hash = hashlib.sha256(content).hexdigest()
    existing_import = db.scalar(
        select(ImportRecord).where(
            ImportRecord.portfolio_id == portfolio_id,
            ImportRecord.content_hash == content_hash,
        )
    )
    if existing_import:
        return {
            "import_id": existing_import.id,
            "rows_imported": existing_import.rows_imported,
            "idempotent_replay": True,
        }
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must use UTF-8 encoding.") from exc
    reader = csv.DictReader(io.StringIO(text))
    headers = {header.strip().lower() for header in (reader.fieldnames or [])}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}.")

    parsed: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        if None in raw_row or any(value is None for value in raw_row.values()):
            errors.append(
                {"row": row_number, "field": "file", "message": "Row field count must match the header."}
            )
            continue
        row = {key.strip().lower(): value.strip() for key, value in raw_row.items()}
        ticker = row.get("ticker", "").upper()
        if not TICKER_PATTERN.fullmatch(ticker):
            errors.append({"row": row_number, "field": "ticker", "message": "Invalid ticker."})
        if ticker in seen:
            errors.append({"row": row_number, "field": "ticker", "message": "Duplicate ticker."})
        seen.add(ticker)
        quantity = _number(row, "quantity", row_number, errors)
        average_cost = _number(row, "average_cost", row_number, errors)
        current_price_text = row.get("current_price")
        current_price = average_cost
        if current_price_text:
            current_price = _number(row, "current_price", row_number, errors)
        parsed.append(
            {
                "ticker": ticker,
                "name": row.get("name") or ticker,
                "quantity": quantity,
                "average_cost": average_cost,
                "current_price": current_price,
                "sector": row.get("sector") or "Unclassified",
                "asset_class": row.get("asset_class") or "Equity",
                "geography": row.get("geography") or "Canada",
                "currency": (row.get("currency") or "CAD").upper(),
            }
        )
    if not parsed:
        errors.append({"row": 1, "field": "file", "message": "CSV contains no data rows."})
    if errors:
        return {"rows_imported": 0, "errors": errors, "idempotent_replay": False}

    existing_symbols = set(
        db.scalars(
            select(Security.symbol)
            .join(Holding, Holding.security_id == Security.id)
            .where(Holding.portfolio_id == portfolio_id, Security.symbol.in_(seen))
        )
    )
    if existing_symbols:
        return {
            "rows_imported": 0,
            "errors": [
                {
                    "row": 1,
                    "field": "ticker",
                    "message": f"Portfolio already contains: {', '.join(sorted(existing_symbols))}.",
                }
            ],
            "idempotent_replay": False,
        }

    try:
        for item in parsed:
            security = db.scalar(select(Security).where(Security.symbol == item["ticker"]))
            if security is None:
                security = Security(
                    symbol=item["ticker"],
                    name=item["name"],
                    sector=item["sector"],
                    asset_class=item["asset_class"],
                    geography=item["geography"],
                    currency=item["currency"],
                )
                db.add(security)
                db.flush()
            db.add(
                Holding(
                    portfolio_id=portfolio_id,
                    security_id=security.id,
                    quantity=item["quantity"],
                    average_cost=item["average_cost"],
                    acquired_at=date.today(),
                )
            )
            db.add(
                MarketPrice(
                    security_id=security.id,
                    price_date=date.today(),
                    close=item["current_price"],
                )
            )
        record = ImportRecord(
            portfolio_id=portfolio_id,
            content_hash=content_hash,
            rows_imported=len(parsed),
        )
        db.add(record)
        db.add(
            AuditEvent(
                actor_id=owner_id,
                action="portfolio.csv_imported",
                resource_type="portfolio",
                resource_id=portfolio_id,
                detail={"rows": len(parsed), "content_hash": content_hash[:12]},
            )
        )
        db.commit()
        return {
            "import_id": record.id,
            "rows_imported": len(parsed),
            "errors": [],
            "idempotent_replay": False,
        }
    except Exception:
        db.rollback()
        raise
