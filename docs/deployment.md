# Deployment runbook

## Local containers

`docker compose up --build` starts PostgreSQL, Redis, the API, Celery worker, and
web app. The API applies Alembic migrations before starting.

## Kubernetes / Azure Kubernetes Service

The `infra/k8s/base` Kustomization expects managed PostgreSQL and Redis
connection strings in an `assetlens-secrets` Secret:

```powershell
kubectl create namespace assetlens
kubectl -n assetlens create secret generic assetlens-secrets `
  --from-literal=DATABASE_URL="<postgresql+psycopg URL>" `
  --from-literal=REDIS_URL="<redis URL>" `
  --from-literal=DEMO_TOKEN="<replace for production>" `
  --from-literal=OPENAI_API_KEY="<optional>"
kubectl apply -k infra/k8s/base
```

Replace the image placeholders in `kustomization.yaml` with immutable registry
digests. Configure TLS and the ingress hostname before public exposure.

For Azure, map PostgreSQL to Azure Database for PostgreSQL Flexible Server,
Redis to Azure Managed Redis, images to Azure Container Registry, OTLP to Azure
Monitor/OpenTelemetry, and workload secrets to Key Vault through workload
identity.

## Release checks

1. CI unit, integration, frontend, and end-to-end jobs pass.
2. Alembic upgrade succeeds against a copy of production schema.
3. Container images are scanned and referenced by digest.
4. Health returns `database=connected` and the expected data date.
5. Run the seeded demo flow and download a PDF.
6. Confirm copilot advice refusals and provider fallback.
7. Review p95 latency, error rate, job failures, and stale-data alerts.

## Rollback

Roll back application images independently. Database downgrades are not the
default rollback mechanism; migrations should be forward-fixable. Scenario and
report jobs are idempotent/status-addressable so orphaned work can be retried
after the application rollback.
