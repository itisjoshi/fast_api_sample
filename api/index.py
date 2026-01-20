from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import numpy as np
from pathlib import Path

app = FastAPI()

DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"

with open(DATA_PATH, "r") as f:
    TELEMETRY = json.load(f)


# ---------- CORS HEADERS ----------
def cors_headers():
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

@app.options("/{path:path}")
async def preflight_handler(path: str):
    return JSONResponse(content={}, headers=cors_headers())


# ---------- MAIN ENDPOINT ----------
@app.post("/")
async def metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms")

    if not regions or threshold is None:
        return JSONResponse(
            content={"error": "regions and threshold_ms are required"},
            headers=cors_headers(),
            status_code=400,
        )

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

    return JSONResponse(content={"metrics": results}, headers=cors_headers())
