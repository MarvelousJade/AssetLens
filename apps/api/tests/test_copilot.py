import pytest


@pytest.mark.parametrize(
    ("question", "expected_tool"),
    [
        ("Why did this portfolio underperform its benchmark?", "get_performance"),
        ("How concentrated is this portfolio?", "get_exposure"),
        ("Which scenario produces the largest estimated loss?", "compare_scenarios"),
    ],
)
def test_copilot_uses_read_only_grounding_tools(client, auth_headers, question, expected_tool):
    response = client.post(
        "/api/copilot/questions",
        headers=auth_headers,
        json={"portfolio_id": "demo-canadian-growth", "question": question},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "deterministic"
    assert expected_tool in [call["name"] for call in payload["tool_calls"]]
    assert payload["citations"]
    assert "[source:" in payload["answer"]


@pytest.mark.parametrize(
    "question",
    [
        "Should I buy more SHOP?",
        "Would you recommend selling TD?",
        "Give me a price target for RY.",
    ],
)
def test_copilot_refuses_personalized_trading_advice(client, auth_headers, question):
    response = client.post(
        "/api/copilot/questions",
        headers=auth_headers,
        json={"portfolio_id": "demo-canadian-growth", "question": question},
    )
    payload = response.json()
    assert payload["mode"] == "guardrail"
    assert payload["tool_calls"] == []
    assert "can’t recommend" in payload["answer"]
