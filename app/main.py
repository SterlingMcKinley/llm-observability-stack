import time
import random
import math
import numpy as np
from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Histogram, Gauge

app = FastAPI(title="LLM Agent Observability Service")

# ==========================================
# 1. PROMETHEUS METRIC DEFINITIONS
# ==========================================
LLM_REQUESTS_TOTAL = Counter(
    'llm_requests_total', 
    'Total number of LLM interactions', 
    ['model', 'status']
)

LLM_TOKEN_USAGE = Counter(
    'llm_tokens_consumed_total', 
    'Total tokens consumed by the LLM application', 
    ['model', 'token_type'] # token_type = prompt or completion
)

LLM_LATENCY = Histogram(
    'llm_latency_seconds', 
    'Time taken for the LLM to return a complete response', 
    ['model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, float("inf"))
)

# LLM Evaluation Unstructured Analytics Gauges
LLM_SEMANTIC_SIMILARITY = Gauge(
    'llm_eval_semantic_similarity', 
    'Cosine similarity score between user intent and model response',
    ['model']
)

LLM_FAITHFULNESS_SCORE = Gauge(
    'llm_eval_faithfulness_score', 
    'Score checking if response is mathematically supported by context chunks (0=Hallucination, 1=Faithful)',
    ['model']
)

# ==========================================
# 2. EVALUATION LOGIC HELPERS
# ==========================================
def calculate_mock_embedding_similarity():
    """
    Simulates checking semantic distance/similarity between prompt intent 
    and output response to identify severe drift or off-topic responses.
    """
    # Emulating a cosine similarity computation output range [0, 1]
    return round(random.uniform(0.65, 0.98), 3)

def evaluate_faithfulness(response_text: str):
    """
    Simulates a lightweight evaluation check for Hallucinations.
    If an agent mentions something completely outside its retrieval context window, 
    the faithfulness score drops significantly.
    """
    # Simulated heuristic analysis: lower score indicates potential hallucination
    if "error" in response_text.lower() or random.random() < 0.08:
        return round(random.uniform(0.1, 0.4), 2)
    return round(random.uniform(0.85, 1.0), 2)

# ==========================================
# 3. APPLICATION ENDPOINTS
# ==========================================
@app.get("/predict")
def generate_llm_response(prompt: str, model: str = "meta-llama3-70b"):
    start_time = time.time()
    
    # 1. Simulate varying operational performance and latency based on model sizes
    processing_delay = random.uniform(0.3, 1.8) if "70b" in model else random.uniform(0.1, 0.6)
    time.sleep(processing_delay)
    
    # Simulate occasional system/API exceptions (5% failure rate)
    if random.random() < 0.05:
        LLM_REQUESTS_TOTAL.labels(model=model, status="error").inc()
        return {"error": "Upstream LLM Provider Timeout or Rate Limit reached."}
    
    # 2. Simulate standard token generation footprints
    prompt_tokens = len(prompt.split()) * 2
    completion_tokens = int(random.uniform(50, 300))
    
    # Mocking sample responses
    mock_responses = [
        f"Based on the retrieved architecture docs, the target cluster requires a VPC peering connection. System context: {prompt[:20]}...",
        "Error handling routes have successfully bypassed the failing node, scaling replicas up.",
        "Query completed. The total execution usage was within budget constraints."
    ]
    generated_text = random.choice(mock_responses)
    
    # 3. Calculate LLM Evaluation Telemetry Metrics
    semantic_sim = calculate_mock_embedding_similarity()
    faithfulness = evaluate_faithfulness(generated_text)
    duration = time.time() - start_time
    
    # 4. Record observations directly to Prometheus Metrics registries
    LLM_REQUESTS_TOTAL.labels(model=model, status="success").inc()
    LLM_TOKEN_USAGE.labels(model=model, token_type="prompt").inc(prompt_tokens)
    LLM_TOKEN_USAGE.labels(model=model, token_type="completion").inc(completion_tokens)
    LLM_LATENCY.labels(model=model).observe(duration)
    
    LLM_SEMANTIC_SIMILARITY.labels(model=model).set(semantic_sim)
    LLM_FAITHFULNESS_SCORE.labels(model=model).set(faithfulness)
    
    return {
        "status": "success",
        "model": model,
        "response": generated_text,
        "telemetry": {
            "latency_seconds": round(duration, 3),
            "tokens_prompt": prompt_tokens,
            "tokens_completion": completion_tokens,
            "eval_semantic_similarity": semantic_sim,
            "eval_faithfulness": faithfulness
        }
    }

@app.get("/metrics")
def metrics():
    """
    Prometheus scraping target endpoint
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)