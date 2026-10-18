import pytest
from traffic.optimizer import choose_green_times, congestion_level

def test_green_time_bounds_and_cycle():
    result = choose_green_times({"North": 20, "East": 5, "South": 10, "West": 0})
    assert set(result) == {"North", "East", "South", "West"}
    assert all(10 <= v <= 45 for v in result.values())
    assert sum(result.values()) == 100

def test_zero_demand_is_even_and_cycle_matches():
    result = choose_green_times({"N": 0, "E": 0}, total_cycle=60)
    assert result == {"N": 30, "E": 30}
    assert sum(result.values()) == 60

def test_cycle_is_clamped_to_feasible_bounds():
    result = choose_green_times({"N": 2, "E": 1}, min_green=10, max_green=20, total_cycle=100)
    assert result == {"N": 20, "E": 20}

def test_invalid_demand_rejected():
    with pytest.raises(ValueError):
        choose_green_times({"North": -1})

def test_congestion_levels():
    assert congestion_level(2) == "Low"
    assert congestion_level(8) == "Medium"
    assert congestion_level(20) == "High"
