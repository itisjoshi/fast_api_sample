from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data at startup
DATA_PATH = Path(__file__).parent.parent / "telemetry.json"

with open(DATA_PATH, "r") as f:
    TELEMETRY = json.load(f)

@app.post("/")
async def metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        return {"error": "regions and threshold_ms are required"}

    results = []

    for region in regions:
        rows = [r for r in TELEMETRY if r["region"] == region]

        if not rows:
            results.append({
                "region": region,
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            })
            continue

        latencies = np.array([r["latency_ms"] for r in rows])
        uptimes = np.array([r["uptime_pct"] for r in rows])

        avg_latency = round(float(latencies.mean()), 2)
        p95_latency = round(float(np.percentile(latencies, 95)), 2)
        avg_uptime = round(float(uptimes.mean()), 3)
        breaches = int((latencies > threshold).sum())

        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })

    return {"metrics": results}
