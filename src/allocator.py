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
    # ranges = [range(0, size + 1, step) for size in displayed_sizes]
    n = len(displayed_sizes)
    ranges = [range(0, target + step, step) for _ in range(n)]
    for combo in itertools.product(*ranges):
        if sum(combo) == target:
            yield list(combo)

def compute_cost(allocation: List[int],
                 ask_prices: List[float],
                 displayed_sizes: List[int],
                 params: Dict[str, float]) -> float:
    """
    Cost = Cash spent + lambda_under * shortfall + lambda_over * overfill
    + theta_queue * queue_risk (currently 0).
    """
    # 1) cash you’d spend if all shares filled at the displayed ask
    cash_spent = sum(a * p for a, p in zip(allocation, ask_prices))

    # 2) how many actually fill (you can’t take more than displayed)
    fills = [min(a, s) for a, s in zip(allocation, displayed_sizes)]
    executed = sum(fills)

    # 3) penalties
    shortfall = max(0, TARGET - executed)  # shares you tried to take but couldn’t
    overfill = max(0, executed - TARGET)  # if you somehow end up > target
    queue_risk = sum(max(0, a - s) for a, s in zip(allocation, displayed_sizes))

    return (cash_spent
            + + params["lambda_under"] * shortfall
            + + params["lambda_over"] * overfill
            + + params["theta_queue"] * queue_risk)

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
        cost = compute_cost(alloc, ask_prices, displayed_sizes, params)
        if cost < best_cost:
            best_cost, best_alloc = cost, alloc

    # fallback—if no exact 5 000 split in 100s, send all to best ask
    if best_alloc is None:
        idx = ask_prices.index(min(ask_prices))
        alloc = [0] * len(ask_prices)
        alloc[idx] = TARGET
        return alloc

    return best_alloc
