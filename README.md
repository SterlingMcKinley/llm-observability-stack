# Cloud-Native Telemetry & Observability Stack for LLM Agents

This project provides a specialized telemetry framework and observability that tracks the lifecycle of an AI agent's execution.

## This Project Features:

- **Application Layer:** A Python application using an LLM (via Amazon Bedrock or any OpenAI-compatible SDK) that generates a response, handles simple retrieval context, and calculates LLM-specific evaluation metrics (semantic similarity, hallucination indicator scores, latency, and token usage).
- **Telemetry Layer:** We will expose these custom metrics via a standard Prometheus client scraping endpoint inside our Python application. This provides a direct, highly reliable telemetry channel without requiring a heavy OpenTelemetry Collector sidecar for a standalone project setup.
- **Observability Layer:** Prometheus scrapes the application metrics at regular intervals, and Grafana connects to Prometheus to visualize your LLM application's health, cost, and response faithfulness.

## Architecture Diagram

## Step-by-Step Instructions to Deploy and Run:

1. Navigate to the root directory containing your configuration files and run:

```bash
 docker-compose up --build -d
```

Verify everything is running perfectly by executing docker-compose ps. There should be three healthy containers running (llm-observability-app, prometheus, and grafana).

2. Since Prometheus collects metrics dynamically over a timeline, we need to generate continuous calls to the mock LLM setup. Run a shell loop in a separate terminal window to send automated trafficto your API endpoint.

- To generate continuous calls I utilized two different shell loops:

- bash randomizer to split the traffic between success and failure for model: meta-llama3-70b

```bash
while true; do
    if [ $((RANDOM % 2)) -eq 0 ]; then
        # 50% chance: Success
        curl "http://localhost:8000/predict?prompt=healthy&model=meta-llama3-70b"
    else
        # 50% chance: Bad Request / Error
        curl "http://localhost:8000/predict?prompt=error&model=meta-llama3-70b"
 fi
    echo ""
    sleep 2
done
```

- bash randomizer to split the traffic between success and failure for model: broken-model

```bash
while true; do
    if [ $((RANDOM % 2)) -eq 0 ]; then
        # 50% chance: Success
        curl "http://localhost:8000/predict?prompt=healthy&model=broken-model"
    else
        # 50% chance: Bad Request / Error
        curl "http://localhost:8000/predict?prompt=error&model=broken-model"
 fi
    echo ""
    sleep 2
done
```

- View the raw text payload being parsed by Prometheus anytime by visiting: http://localhost:8000/metrics.

3. Configure the Grafana Dashboard

- Navigate to the Grafana dashboard interface: http://localhost:3000. (Login: admin / admin)
- Connect Prometheus as your Data Source: Go to Connections > Data Sources > Click Add data source.
- Select Prometheus.
- Set the Connection URL precisely to: http://prometheus:9090 (this utilizes internal Docker networking).
- Scroll down and click Save & test. You should see a green success checkmark.

4. Build Custom LLM Monitoring Dashboard

- Click on the Dashboards icon on the top-left menu, click New > New Dashboard, and add visualization panels using the following highly optimized PromQL queries:
  - _Panel 1: Global LLM Request Success vs Error Rates (Time Series)_

  ```bash
  sum(rate(llm_requests_total[1m])) by (status, model)
  ```

  - _Panel 2: P95 Inference Latency (Time Series)_

  ```bash
  histogram_quantile(0.95, sum(rate(llm_latency_seconds_bucket[5m])) by (le, model))
  ```

  - _Panel 3: Real-Time Hallucination Tracking / Faithfulness Indicator (Gauge)_

  ```bash
  avg(llm_eval_faithfulness_score) by (model)
  ```

  - _Panel 4: Running Token Consumption Rate (Stat or Bar Gauge)_

  ```bash
  sum(increase(llm_tokens_consumed_total[5m])) by (token_type)
  ```

5. Once the dashboard is complete, SAVE IT. As the background traffic loop continues to run, the live dashboard will track real-time API latency, operational errors, token consumption costs, and automated response quality scores.

## Issues / Lessons Learned
