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
