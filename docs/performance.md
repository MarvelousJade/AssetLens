# Local performance baseline

AssetLens has an absolute local latency baseline so future changes can be
compared against recorded measurements. It does not yet claim any performance
improvement.

## Recorded run

Measured on July 29, 2026 at 15:10 UTC:

- Windows 11, Python 3.12.10
- AMD64 Family 23 Model 113 processor
- temporary SQLite database populated with the seeded eight-holding portfolio
- FastAPI `TestClient`, without network transport
- deterministic copilot provider, without an external model request
- five warm-up requests before each measured operation

| Operation | Iterations | Mean | p50 | p95 | Derived requests/s |
| --- | ---: | ---: | ---: | ---: | ---: |
| Holdings snapshot | 100 | 33.319 ms | 23.612 ms | 70.528 ms | 30.01 |
| Performance analytics | 100 | 43.948 ms | 32.594 ms | 81.544 ms | 22.75 |
| Exposure analytics | 100 | 34.845 ms | 24.379 ms | 70.527 ms | 28.70 |
| Deterministic copilot | 100 | 39.180 ms | 29.074 ms | 75.988 ms | 25.52 |
| PDF report creation | 10 | 149.029 ms | 152.334 ms | 158.745 ms | 6.71 |

The requests-per-second column is the reciprocal of mean latency from a
single-threaded run. It is not a concurrent load-test result.

## Reproduce

From `apps/api`, with development dependencies installed:

```powershell
python scripts/benchmark_api.py `
  --iterations 100 `
  --report-iterations 10 `
  --warmup-iterations 5
```

The script creates and removes `apps/api/.tmp/assetlens-benchmark.db`. Use
`--output <path>` to retain the complete JSON result, including environment
metadata.

## Interpretation limits

- Results include FastAPI routing, dependency injection, serialization, and
  SQLite access, but exclude network latency and a separate application server.
- They do not represent Render, PostgreSQL, Celery, Redis, Kubernetes, or live
  OpenAI performance.
- Local scheduling, antivirus activity, power settings, and hardware can
  materially change timings.
- A verified improvement percentage requires running the same command and
  environment against an explicitly identified baseline and candidate revision.
