from typing import Dict, List
import itertools
import pandas as pd

TARGET = 5000

def generate_allocations(displayed_sizes: List[int],
                         step: int = 100,
                         target: int = TARGET) -> List[List[int]]:
    """
    Enumerate all ways to split `target` shares into chunks of size `step`,
    without exceeding each venue's displayed size.
    """
    ranges = [range(0, size + 1, step) for size in displayed_sizes]
    for combo in itertools.product(*ranges):
        if sum(combo) == target:
            yield list(combo)

def compute_cost(allocation: List[int],
                 ask_prices: List[float],
                 params: Dict[str, float]) -> float:
    """
    Cost = Cash spent + lambda_under * shortfall + lambda_over * overfill
    + theta_queue * queue_risk (currently 0).
    """
    cash_spent = sum(a * p for a, p in zip(allocation, ask_prices))
    total = sum(allocation)
    shortfall = max(0, TARGET - total)
    overfill  = max(0, total - TARGET)
    queue_risk = 0.0  # placeholder (no queue‐position model)
    return (cash_spent
            + params.get("lambda_under", 0.0) * shortfall
            + params.get("lambda_over", 0.0)  * overfill
            + params.get("theta_queue", 0.0)  * queue_risk)

def allocate(snapshot: pd.DataFrame,
             params: Dict[str, float],
             step: int = 100) -> List[int]:
    """
    Given one snapshot (one timestamp, multiple venues),
    return the 5 000-share split minimizing expected cost.
    """
    ask_prices     = snapshot["ask_px_00"].tolist()
    displayed_sizes = snapshot["ask_sz_00"].tolist()

    best_cost = float("inf")
    best_alloc = None

    for alloc in generate_allocations(displayed_sizes, step, TARGET):
        cost = compute_cost(alloc, ask_prices, params)
        if cost < best_cost:
            best_cost, best_alloc = cost, alloc

    # fallback—if no exact 5 000 split in 100s, send all to best ask
    if best_alloc is None:
        idx = ask_prices.index(min(ask_prices))
        alloc = [0] * len(ask_prices)
        alloc[idx] = TARGET
        return alloc

    return best_alloc
