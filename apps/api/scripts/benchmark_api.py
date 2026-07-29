"""Measure a reproducible local API baseline without making production claims."""

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def percentile(samples: list[float], percentile_value: float) -> float:
    ordered = sorted(samples)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[index]


def measure(
    operation: Callable[[], Any],
    iterations: int,
    warmup_iterations: int,
) -> dict[str, float | int]:
    for _ in range(warmup_iterations):
        response = operation()
        response.raise_for_status()

    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        response = operation()
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.raise_for_status()
        samples.append(elapsed_ms)

    mean_ms = statistics.fmean(samples)
    return {
        "iterations": iterations,
        "mean_ms": round(mean_ms, 3),
        "p50_ms": round(percentile(samples, 0.50), 3),
        "p95_ms": round(percentile(samples, 0.95), 3),
        "requests_per_second": round(1000 / mean_ms, 2),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark representative AssetLens endpoints through FastAPI TestClient."
    )
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--report-iterations", type=int, default=10)
    parser.add_argument("--warmup-iterations", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        help="Optionally write the JSON result to this path.",
    )
    args = parser.parse_args()
    if args.iterations < 1 or args.report_iterations < 1:
        parser.error("Iteration counts must be positive.")
    if args.warmup_iterations < 0:
        parser.error("Warm-up iterations cannot be negative.")
    return args


def main() -> None:
    args = parse_args()
    api_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(api_root))
    benchmark_temp_root = api_root / ".tmp"
    benchmark_temp_root.mkdir(exist_ok=True)
    database_path = benchmark_temp_root / "assetlens-benchmark.db"
    database_path.unlink(missing_ok=True)

    os.environ["DATABASE_URL"] = "sqlite:///./.tmp/assetlens-benchmark.db"
    os.environ["COPILOT_PROVIDER"] = "deterministic"
    os.environ["TASK_MODE"] = "local"

    from fastapi.testclient import TestClient

    from app.database import engine
    from app.main import app

    headers = {"Authorization": "Bearer assetlens-demo-token"}
    portfolio_path = "/api/portfolios/demo-canadian-growth"

    try:
        with TestClient(app) as client:
            operations: dict[str, tuple[Callable[[], Any], int]] = {
                "holdings": (
                    lambda: client.get(f"{portfolio_path}/holdings", headers=headers),
                    args.iterations,
                ),
                "performance": (
                    lambda: client.get(f"{portfolio_path}/performance", headers=headers),
                    args.iterations,
                ),
                "exposure": (
                    lambda: client.get(f"{portfolio_path}/exposure", headers=headers),
                    args.iterations,
                ),
                "copilot_deterministic": (
                    lambda: client.post(
                        "/api/copilot/questions",
                        headers=headers,
                        json={
                            "portfolio_id": "demo-canadian-growth",
                            "question": "How concentrated is this portfolio?",
                        },
                    ),
                    args.iterations,
                ),
                "pdf_report": (
                    lambda: client.post(f"{portfolio_path}/reports", headers=headers),
                    args.report_iterations,
                ),
            }
            results = {
                name: measure(operation, iterations, args.warmup_iterations)
                for name, (operation, iterations) in operations.items()
            }
    finally:
        engine.dispose()
        database_path.unlink(missing_ok=True)

    payload = {
        "measured_at": datetime.now(UTC).isoformat(),
        "scope": "Local FastAPI TestClient baseline; no network or production infrastructure.",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "not reported",
            "database": "Temporary SQLite",
            "copilot_provider": "deterministic",
        },
        "methodology": {
            "warmup_iterations_per_operation": args.warmup_iterations,
            "timing": "Wall-clock time measured with time.perf_counter.",
            "throughput": "Single-threaded reciprocal of mean latency; not a load test.",
        },
        "results": results,
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
