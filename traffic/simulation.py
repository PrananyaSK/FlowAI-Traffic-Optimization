"""Reproducible multi-intersection traffic-control simulation for project evaluation."""
import random
import pandas as pd
from traffic.optimizer import choose_green_times

APPROACHES = ["North", "East", "South", "West"]

def run_simulation(minutes: int = 30, seed: int = 7, intersections: int = 4):
    """Compare fixed-time and adaptive policies on the same synthetic demand profile.

    This is a simplified queueing simulation for academic comparison, not a calibrated
    digital twin of a real road network.
    """
    rng = random.Random(seed)
    records = []
    # Demand changes over time and differs by intersection.
    for ix in range(1, intersections + 1):
        queues_fixed = {a: 0.0 for a in APPROACHES}
        queues_adapt = {a: 0.0 for a in APPROACHES}
        for minute in range(minutes):
            demand = {}
            for a in APPROACHES:
                base = 5 + 5 * (1 if minute % 15 in range(5, 11) else 0)
                demand[a] = max(0, rng.gauss(base + (ix % 3), 2.5))
            adaptive_green = choose_green_times(demand, min_green=8, max_green=35, total_cycle=100)
            for policy, queues in [("Fixed-time", queues_fixed), ("Adaptive", queues_adapt)]:
                for a in APPROACHES:
                    arrivals = demand[a]
                    if policy == "Fixed-time":
                        green = 25
                    else:
                        green = adaptive_green[a]
                    # Approximate service capacity: more green time clears more vehicles.
                    served = min(queues[a] + arrivals, green * 0.28)
                    queues[a] = max(0.0, queues[a] + arrivals - served)
                    records.append({
                        "minute": minute + 1,
                        "intersection": f"Junction {ix}",
                        "policy": policy,
                        "approach": a,
                        "arrivals": round(arrivals, 2),
                        "green_seconds": int(green),
                        "queue": round(queues[a], 2),
                        "estimated_wait_seconds": round(queues[a] * 2.2, 2),
                        "vehicles_served": round(served, 2),
                    })
    return pd.DataFrame(records)

def summarize(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame()
    return (results.groupby("policy", as_index=False)
            .agg(avg_queue=("queue", "mean"),
                 avg_wait_seconds=("estimated_wait_seconds", "mean"),
                 total_served=("vehicles_served", "sum"),
                 avg_green_seconds=("green_seconds", "mean")))
