# API guide

Interactive OpenAPI documentation is available at `/docs` while the API is
running. Except for health, requests require:

```http
Authorization: Bearer assetlens-demo-token
```

Core endpoints:

- `GET /api/portfolios`
- `POST /api/portfolios`
- `POST /api/portfolios/{id}/imports`
- `GET /api/portfolios/{id}/holdings`
- `GET /api/portfolios/{id}/performance`
- `GET /api/portfolios/{id}/risk`
- `GET /api/portfolios/{id}/exposure`
- `GET /api/portfolios/{id}/attribution`
- `POST /api/portfolios/{id}/scenarios`
- `GET /api/scenario-runs/{id}`
- `POST /api/scenario-runs/{id}/cancel`
- `POST /api/copilot/questions`
- `POST /api/portfolios/{id}/reports`
- `GET /api/reports/{id}`
- `GET /api/securities`
- `GET|POST|DELETE /api/watchlist`
- `GET|POST /api/alerts`
- `GET /api/health`

## Error contract

FastAPI returns `{"detail": ...}`. Validation errors use HTTP 422,
authentication errors 401, missing owned resources 404, and invalid state
transitions 409. CSV row errors identify the row, field, and message.

## CSV validation

Imports validate every row before writing holdings, securities, prices, the
import record, or its audit event. A mixed valid/invalid file is rejected as a
whole with HTTP 422.

- `quantity`, `average_cost`, and any supplied `current_price` must be finite
  positive numbers. `NaN`, infinities, and values overflowing to infinity (such
  as `1e309`) are rejected.
- Each data row must contain the same number of fields as the header. Extra or
  missing fields produce a row-level `file` error rather than a server error.
- An explicitly blank optional `current_price` field is allowed and defaults to
  `average_cost`; a truncated row is not equivalent to an explicit blank field.
- Exact-byte replays of successfully imported files retain the existing
  idempotent response. This is not a claim of concurrent-import safety.
