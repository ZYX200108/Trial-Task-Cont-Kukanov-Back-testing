import itertools
from typing import Dict, List

TARGET = 5000

def generate_allocations(displayed_sizes: List[int],
                         step: int = 100,
                         target: int = TARGET) -> List[List[int]]:
    """
    Enumerate all ways to request `target` shares in chunks of `step`,
    WITHOUT capping at displayed size, so over-requests incur penalties.
    """
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
    Cost = theoretical cash + lambda_under * shortfall
           + lambda_over * overfill + theta_queue * queue_risk
    """
    # 1) pretend cash if all requested shares fill
    cash_spent = sum(a * p for a, p in zip(allocation, ask_prices))

    # 2) actual fills limited by displayed size
    fills    = [min(a, s) for a, s in zip(allocation, displayed_sizes)]
    executed = sum(fills)

    # 3) penalties
    shortfall  = max(0, TARGET - executed)                    # unfilled
    overfill   = max(0, executed - TARGET)                    # should be zero
    queue_risk = sum(max(0, a - s) for a, s in zip(allocation, displayed_sizes))

    return (
        cash_spent
        + params["lambda_under"] * shortfall
        + params["lambda_over"]  * overfill
        + params["theta_queue"]  * queue_risk
    )

def allocate(snapshot,
             params: Dict[str, float],
             step: int = 100) -> List[int]:
    """
    Single static allocation on one snapshot:
    returns a list summing to TARGET that minimizes compute_cost().
    """
    ask_prices      = snapshot["ask_px_00"].tolist()
    displayed_sizes = snapshot["ask_sz_00"].tolist()

    best_cost  = float("inf")
    best_alloc = None

    for alloc in generate_allocations(displayed_sizes, step, TARGET):
        cost = compute_cost(alloc, ask_prices, displayed_sizes, params)
        if cost < best_cost:
            best_cost, best_alloc = cost, alloc

    # fallback: send all to best ask
    if best_alloc is None:
        idx = ask_prices.index(min(ask_prices))
        alloc = [0] * len(ask_prices)
        alloc[idx] = TARGET
        return alloc

    return best_alloc
