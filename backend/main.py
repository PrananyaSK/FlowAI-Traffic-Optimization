from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict
from traffic.optimizer import choose_green_times, adaptive_decision

app = FastAPI(
    title="AI Traffic Flow Optimization API",
    description="Educational API for adaptive traffic signal timing and demand analysis.",
    version="1.0.0",
)

class DemandRequest(BaseModel):
    demand: Dict[str, float] = Field(..., examples=[{"North": 18, "East": 7, "South": 12, "West": 4}])

@app.get("/")
def root():
    return {"name": "AI Traffic Flow Optimization System", "status": "running", "docs": "/docs"}

@app.post("/optimize")
def optimize(req: DemandRequest):
    times = choose_green_times(req.demand)
    decision = adaptive_decision(req.demand)
    return {"green_times_seconds": times, "recommended_phase": decision.phase,
            "recommended_green_seconds": decision.green_seconds, "reason": decision.reason}

@app.get("/health")
def health():
    return {"status": "ok"}
