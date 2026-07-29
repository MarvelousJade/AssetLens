from io import BytesIO

import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/api/portfolios/demo-canadian-growth/holdings",
        "/api/portfolios/demo-canadian-growth/performance",
        "/api/portfolios/demo-canadian-growth/risk",
        "/api/portfolios/demo-canadian-growth/exposure",
        "/api/portfolios/demo-canadian-growth/attribution",
    ],
)
def test_analytics_endpoints_hide_another_users_portfolio(
    client, set_authenticated_user, path
):
    set_authenticated_user("another-user")

    response = client.get(path)

    assert response.status_code == 404


def test_mutating_workflows_reject_another_users_portfolio(
    client, set_authenticated_user
):
    set_authenticated_user("another-user")

    imported = client.post(
        "/api/portfolios/demo-canadian-growth/imports",
        files={
            "file": (
                "holdings.csv",
                BytesIO(b"ticker,quantity,average_cost\nABC,1,10\n"),
                "text/csv",
            )
        },
    )
    scenario = client.post(
        "/api/portfolios/demo-canadian-growth/scenarios",
        json={
            "name": "Unauthorized scenario",
            "scenario_type": "equity_decline",
            "shocks": {},
        },
    )
    copilot = client.post(
        "/api/copilot/questions",
        json={
            "portfolio_id": "demo-canadian-growth",
            "question": "How concentrated is this portfolio?",
        },
    )
    report = client.post(
        "/api/portfolios/demo-canadian-growth/reports"
    )

    assert imported.status_code == 404
    assert scenario.status_code == 404
    assert copilot.status_code == 404
    assert report.status_code == 404


def test_scenario_and_report_downloads_are_owner_scoped(
    client, auth_headers, set_authenticated_user
):
    scenario = client.post(
        "/api/portfolios/demo-canadian-growth/scenarios",
        headers=auth_headers,
        json={
            "name": "Owner-scoped scenario",
            "scenario_type": "technology_decline",
            "shocks": {},
        },
    )
    report = client.post(
        "/api/portfolios/demo-canadian-growth/reports",
        headers=auth_headers,
    )
    assert scenario.status_code == 202
    assert report.status_code == 201

    set_authenticated_user("another-user")

    scenario_read = client.get(scenario.json()["poll_url"])
    report_read = client.get(report.json()["download_url"])

    assert scenario_read.status_code == 404
    assert report_read.status_code == 404


def test_each_user_only_lists_and_reads_their_own_portfolios(
    client, set_authenticated_user
):
    set_authenticated_user("another-user")
    created = client.post(
        "/api/portfolios",
        json={"name": "Another user's portfolio"},
    )
    assert created.status_code == 201
    another_portfolio_id = created.json()["id"]

    other_list = client.get("/api/portfolios")
    assert [item["id"] for item in other_list.json()] == [
        another_portfolio_id
    ]

    set_authenticated_user("demo-user")

    demo_list = client.get("/api/portfolios")
    assert another_portfolio_id not in {
        item["id"] for item in demo_list.json()
    }
    denied = client.get(
        f"/api/portfolios/{another_portfolio_id}/holdings"
    )
    assert denied.status_code == 404
