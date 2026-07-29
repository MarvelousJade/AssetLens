from io import BytesIO


def test_private_portfolio_routes_require_authentication(client):
    response = client.get("/api/portfolios")
    assert response.status_code == 401


def test_seeded_dashboard_contract(client, auth_headers):
    portfolios = client.get("/api/portfolios", headers=auth_headers)
    assert portfolios.status_code == 200
    assert portfolios.json()[0]["id"] == "demo-canadian-growth"

    holdings = client.get("/api/portfolios/demo-canadian-growth/holdings", headers=auth_headers)
    assert holdings.status_code == 200
    assert len(holdings.json()["holdings"]) == 8
    assert holdings.json()["summary"]["market_value"] > 0


def test_scenario_job_returns_grounded_impact(client, auth_headers):
    created = client.post(
        "/api/portfolios/demo-canadian-growth/scenarios",
        headers=auth_headers,
        json={
            "name": "Technology drawdown",
            "scenario_type": "technology_decline",
            "shocks": {},
        },
    )
    assert created.status_code == 202
    run = client.get(created.json()["poll_url"], headers=auth_headers)
    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["result"]["estimated_impact"] < 0
    assert len(run.json()["result"]["assumptions"]) == 3


def test_csv_import_is_atomic_and_idempotent(client, auth_headers):
    portfolio = client.post(
        "/api/portfolios",
        headers=auth_headers,
        json={"name": "Imported test portfolio"},
    ).json()
    invalid_csv = b"ticker,quantity,average_cost\nABC,-2,10\n"
    invalid = client.post(
        f"/api/portfolios/{portfolio['id']}/imports",
        headers=auth_headers,
        files={"file": ("holdings.csv", BytesIO(invalid_csv), "text/csv")},
    )
    assert invalid.status_code == 422
    holdings = client.get(f"/api/portfolios/{portfolio['id']}/holdings", headers=auth_headers).json()
    assert holdings["holdings"] == []

    valid_csv = (
        b"ticker,name,quantity,average_cost,current_price,sector\n"
        b"ABC,Example Corp,12,10.50,11.25,Industrials\n"
    )
    first = client.post(
        f"/api/portfolios/{portfolio['id']}/imports",
        headers=auth_headers,
        files={"file": ("holdings.csv", BytesIO(valid_csv), "text/csv")},
    )
    replay = client.post(
        f"/api/portfolios/{portfolio['id']}/imports",
        headers=auth_headers,
        files={"file": ("holdings.csv", BytesIO(valid_csv), "text/csv")},
    )
    assert first.status_code == 200
    assert first.json()["rows_imported"] == 1
    assert replay.json()["idempotent_replay"] is True
    holdings = client.get(
        f"/api/portfolios/{portfolio['id']}/holdings",
        headers=auth_headers,
    )
    assert len(holdings.json()["holdings"]) == 1


def test_report_is_a_real_pdf(client, auth_headers):
    created = client.post("/api/portfolios/demo-canadian-growth/reports", headers=auth_headers)
    assert created.status_code == 201
    report = client.get(created.json()["download_url"], headers=auth_headers)
    assert report.status_code == 200
    assert report.headers["content-type"] == "application/pdf"
    assert report.content.startswith(b"%PDF")
    assert len(report.content) > 2000
