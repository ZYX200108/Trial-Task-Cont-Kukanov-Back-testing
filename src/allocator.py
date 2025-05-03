# src/allocator.py
from typing import Dict, List
import pandas as pd
import numpy as np

TARGET = 5000


def allocate(snapshot: pd.DataFrame,
             params: Dict[str, float],
             step: int = 100) -> List[int]:
    """
    Implement the exact algorithm from allocator_pseudocode.txt
    """
    order_size = TARGET
    venues = snapshot
    lambda_over = params["lambda_over"]
    lambda_under = params["lambda_under"]
    theta_queue = params["theta_queue"]

    n_venues = len(venues)
    ask_prices = venues["ask_px_00"].tolist()
    ask_sizes = venues["ask_sz_00"].tolist()

    # Following the pseudocode exactly:
    # step ← 100
    # splits ← [[]]
    splits = [[]]

    # for v in 0 .. len(venues)-1:
    for v in range(n_venues):
        new_splits = []
        for alloc in splits:
            used = sum(alloc)
            max_v = min(order_size - used, ask_sizes[v])
            # for q in 0 .. max_v step step:
            for q in range(0, max_v + 1, step):
                new_splits.append(alloc + [q])
        splits = new_splits

    best_cost = float('inf')
    best_split = []

    for alloc in splits:
        if sum(alloc) != order_size:
            continue
        cost = compute_cost(alloc, venues, order_size, lambda_over, lambda_under, theta_queue)
        if cost < best_cost:
            best_cost = cost
            best_split = alloc

    # If no valid allocation found, create default
    if not best_split:
        idx = ask_prices.index(min(ask_prices))
        best_split = [0] * n_venues
        best_split[idx] = order_size

    return best_split


def compute_cost(split: List[int],
                 venues: pd.DataFrame,
                 order_size: int,
                 lambda_over: float,
                 lambda_under: float,
                 theta_queue: float) -> float:
    """
    Implement compute_cost exactly as in pseudocode
    """
    ask_prices = venues["ask_px_00"].tolist()
    ask_sizes = venues["ask_sz_00"].tolist()

    # Assuming fees and rebates are 0 as per pseudocode
    fees = [0.0] * len(venues)
    rebates = [0.0] * len(venues)

    executed = 0
    cash_spent = 0

    # for i in 0 .. len(venues)-1:
    for i in range(len(venues)):
        exe = min(split[i], ask_sizes[i])
        executed += exe
        cash_spent += exe * (ask_prices[i] + fees[i])
        maker_rebate = max(split[i] - exe, 0) * rebates[i]
        cash_spent -= maker_rebate

    underfill = max(order_size - executed, 0)
    overfill = max(executed - order_size, 0)
    risk_pen = theta_queue * (underfill + overfill)
    cost_pen = lambda_under * underfill + lambda_over * overfill

    return cash_spent + risk_pen + cost_pen