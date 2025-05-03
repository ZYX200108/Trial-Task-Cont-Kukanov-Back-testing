import itertools
from typing import Dict, List
import pandas as pd

TARGET = 5000


def generate_allocations(n_venues: int, step: int = 100) -> List[List[int]]:
    ranges = [range(0, TARGET + step, step) for _ in range(n_venues)]
    for combo in itertools.product(*ranges):
        if sum(combo) == TARGET:
            yield list(combo)


def compute_cost(allocation: List[int],
                 ask0: List[float],
                 disp0: List[int],
                 snapshots: List[pd.DataFrame],
                 params: Dict[str, float]) -> float:
    # Simulate limit order fills across all snapshots
    rem = allocation.copy()
    for snap in snapshots:
        depths = snap["ask_sz_00"].tolist()
        rem = [max(0, r - d) for r, d in zip(rem, depths)]

    filled = TARGET - sum(rem)
    cash_cost = sum(a * p for a, p in zip(allocation, ask0))

    shortfall = max(0, TARGET - filled)
    queue_risk = sum(max(0, a - d0) for a, d0 in zip(allocation, disp0))

    return cash_cost + params["lambda_under"] * shortfall + params["theta_queue"] * queue_risk


def allocate(snapshots: List[pd.DataFrame],
             params: Dict[str, float],
             step: int = 100) -> List[int]:
    if not snapshots:
        return []

    snap0 = snapshots[0]
    ask0 = snap0["ask_px_00"].tolist()
    disp0 = snap0["ask_sz_00"].tolist()
    n_venues = len(ask0)

    best_cost = float("inf")
    best_alloc = None

    for alloc in generate_allocations(n_venues, step):
        cost = compute_cost(alloc, ask0, disp0, snapshots, params)
        if cost < best_cost:
            best_cost, best_alloc = cost, alloc

    if best_alloc is None:
        idx = ask0.index(min(ask0))
        return [TARGET if i == idx else 0 for i in range(n_venues)]

    return best_alloc