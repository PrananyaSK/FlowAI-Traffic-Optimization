"""Explainable adaptive green-time allocation for an educational traffic prototype."""
from dataclasses import dataclass
from math import isfinite
from typing import Dict

@dataclass
class SignalDecision:
    phase: str
    green_seconds: int
    reason: str

def choose_green_times(demand: Dict[str, float], min_green: int = 10,
                       max_green: int = 45, total_cycle: int = 100) -> Dict[str, int]:
    """Allocate integer green times within bounds and as close as possible to the cycle.

    The returned sum equals the feasible target cycle whenever integer bounds permit it.
    A feasible target is clamped to [number_of_phases*min_green, number_of_phases*max_green].
    """
    if not demand:
        return {}
    if min_green < 1 or max_green < min_green or total_cycle < 1:
        raise ValueError("Require 1 <= min_green <= max_green and total_cycle >= 1")
    keys = list(demand)
    weights = {}
    for key, value in demand.items():
        number = float(value)
        if not isfinite(number) or number < 0:
            raise ValueError(f"Demand for {key!r} must be a finite, non-negative number")
        weights[key] = number
    n = len(keys)
    target = min(max(int(total_cycle), n * min_green), n * max_green)
    remaining = target - n * min_green
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        weights = {key: 1.0 for key in keys}
        weight_sum = float(n)
    exact = {key: remaining * weights[key] / weight_sum for key in keys}
    extra = {key: min(max_green-min_green, int(exact[key])) for key in keys}
    left = remaining - sum(extra.values())
    order = sorted(keys, key=lambda key: (exact[key] - int(exact[key]), weights[key]), reverse=True)
    while left > 0:
        eligible = [key for key in order if extra[key] < max_green-min_green]
        if not eligible:
            break
        for key in eligible:
            if left <= 0:
                break
            extra[key] += 1
            left -= 1
    return {key: min_green + extra[key] for key in keys}

def congestion_level(queue: float) -> str:
    if queue < 5:
        return "Low"
    if queue < 12:
        return "Medium"
    return "High"

def adaptive_decision(demand: Dict[str, float]) -> SignalDecision:
    if not demand:
        return SignalDecision("N/A", 10, "No traffic demand was supplied.")
    cleaned = {key: max(0.0, float(value)) for key, value in demand.items()}
    phase = max(cleaned, key=cleaned.get)
    green = min(45, max(10, int(10 + cleaned[phase] * 1.5)))
    return SignalDecision(phase, green, f"{phase} has the highest estimated demand ({cleaned[phase]:.0f}).")
