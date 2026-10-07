import pytest
from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import AuditEvent, Holding, ImportRecord, MarketPrice, Security


def _import_table_counts():
    with SessionLocal() as db:
        return {
            model.__tablename__: db.scalar(select(func.count()).select_from(model))
            for model in (Holding, Security, MarketPrice, ImportRecord, AuditEvent)
        }


def _assert_rejected_without_writes(client, auth_headers, content, field):
    created = client.post(
        "/api/portfolios", headers=auth_headers, json={"name": "CSV validation regression"}
    )
    assert created.status_code == 201
    portfolio_id = created.json()["id"]
    before = _import_table_counts()
    response = client.post(
        f"/api/portfolios/{portfolio_id}/imports",
        headers=auth_headers,
        files={"file": ("holdings.csv", content, "text/csv")},
    )
    assert response.status_code == 422
    result = response.json()["detail"]
    assert result["rows_imported"] == 0
    assert any(error["row"] == 3 and error["field"] == field for error in result["errors"])
    assert _import_table_counts() == before
    holdings = client.get(f"/api/portfolios/{portfolio_id}/holdings", headers=auth_headers)
    assert holdings.status_code == 200
    assert holdings.json()["holdings"] == []


@pytest.mark.parametrize("field", ["quantity", "average_cost", "current_price"])
@pytest.mark.parametrize("value", ["NaN", "inf", "-inf", "1e309"])
def test_nonfinite_csv_values_reject_entire_import(client, auth_headers, field, value):
    row = {"quantity": "2", "average_cost": "10", "current_price": "12"}
    row[field] = value
    content = (
        "ticker,quantity,average_cost,current_price\n"
        "VALIDCSV,3,10,12\n"
        f"INVALIDCSV,{row['quantity']},{row['average_cost']},{row['current_price']}\n"
    ).encode()
    _assert_rejected_without_writes(client, auth_headers, content, field)


@pytest.mark.parametrize("row", ["INVALIDCSV,2,10,12,extra", "INVALIDCSV,2,10"])
def test_malformed_csv_row_rejects_entire_import(client, auth_headers, row):
    content = (
        "ticker,quantity,average_cost,current_price\n"
        "VALIDCSV,3,10,12\n"
        f"{row}\n"
    ).encode()
    _assert_rejected_without_writes(client, auth_headers, content, "file")


def test_blank_optional_price_is_not_a_missing_csv_field(client, auth_headers):
    created = client.post(
        "/api/portfolios", headers=auth_headers, json={"name": "Blank optional price"}
    )
    assert created.status_code == 201
    portfolio_id = created.json()["id"]
    response = client.post(
        f"/api/portfolios/{portfolio_id}/imports",
        headers=auth_headers,
        files={
            "file": (
                "holdings.csv",
                b"ticker,quantity,average_cost,current_price\nBLANKPRICE,2,10,\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    assert response.json()["rows_imported"] == 1
    holdings = client.get(f"/api/portfolios/{portfolio_id}/holdings", headers=auth_headers).json()
    assert holdings["holdings"][0]["current_price"] == 10
    assert holdings["summary"]["market_value"] == 20
