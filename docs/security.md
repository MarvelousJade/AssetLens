# Security and AI guardrails

## Trust boundaries

The browser is untrusted. Portfolio ownership is checked in the API, not inferred
from a frontend route or request body. The included demo token is deliberately
public and grants access to a shared demonstration workspace, including portfolio
creation, CSV imports, scenario execution, and report generation. It is not a
read-only workspace: use fictional data only. Production deployments must replace
it with OIDC/JWT validation and a per-user subject.
The resolved owner is a required service-layer argument for imports, analytics,
scenarios, copilot tools, and reports; there is no implicit demo-owner fallback
inside those paths.

## Implemented controls

- Authentication is required for every portfolio, research, report, scenario,
  alert, watchlist, and copilot route.
- Ownership filters are part of resource queries, including scenario and report
  downloads.
- CSV files are size-limited, UTF-8 decoded, schema checked, and fully validated
  before a transaction writes data.
- Import content hashes provide idempotency and avoid duplicate processing.
- SQLAlchemy parameterizes queries.
- CORS allows only the configured web origin.
- No secret is committed; deployment manifests reference a separately managed
  `assetlens-secrets` object.
- Audit events record portfolio creation, imports, scenario completion, report
  generation, and every copilot analytics call.

## Copilot controls

- Model-visible tools can only read performance, exposure, attribution, and
  scenario results.
- The model never receives a database connection and cannot mutate a portfolio.
- Tool arguments are checked against the already-authorized portfolio ID.
- Metrics are calculated by application code; the model only explains returned
  values.
- The tool loop is bounded to four rounds.
- The system prompt treats retrieved/tool text as untrusted data.
- Numerical answers carry source identifiers and dates.
- Requests for personalized buy, sell, hold, price-target, or security
  recommendations are refused before model invocation.
- Provider failures degrade to a deterministic grounded answer.

## Production hardening

Before accepting real customer data: replace the demo token with Entra ID or
another OIDC provider; use a key vault and workload identity; add row-level
security; encrypt report blobs; configure retention and deletion policies; rate
limit by authenticated subject; scan uploads; and send audit events to an
append-only security store.
