# Prometheus and Grafana for the Guardrails server

A ready-to-run Prometheus + Grafana pair that scrapes the non-streaming
admission-queue metrics exposed by `nemoguardrails server --metrics-exporter prometheus`
and provisions a dashboard for them.

The full walkthrough, including how to start the server, lives in the docs:
[Prometheus and Grafana for the Guardrails Server](../../../docs/observability/metrics/server-prometheus-grafana.mdx).

## Quick start

1. Start a Guardrails server on the host with the exporter enabled. The config
   must set `metrics.enabled: true` and the IORails engine must be active:

   ```bash
   pip install "nemoguardrails[server]"
   export NEMO_GUARDRAILS_IORAILS_ENGINE=1
   nemoguardrails server --config ./config --metrics-exporter prometheus
   ```

2. Start Prometheus and Grafana from this directory:

   ```bash
   docker compose up -d
   ```

3. Open Grafana at <http://localhost:3000>. Anonymous viewers can see the
   provisioned **NeMo Guardrails - Non-Streaming Admission Queue** dashboard in
   the **NeMo Guardrails** folder without signing in; the Prometheus data source
   is pre-configured. To edit anything, sign in as `admin` and set a password
   when Grafana prompts for one.

Both containers publish their ports on `127.0.0.1` only, so they are not
reachable from other machines.

Prometheus scrapes `host.docker.internal:9464`. Edit
`prometheus/prometheus.yml` if the server runs on another host or port.

## What is on the dashboard

| Prometheus metric | Panel |
|---|---|
| `guardrails_nonstream_queued` | Queued vs. active requests |
| `guardrails_nonstream_active` | Queued vs. active requests |
| `guardrails_nonstream_rejections_total` | Rejections (last 5m), Rejection rate |

## Clean up

```bash
docker compose down
```
