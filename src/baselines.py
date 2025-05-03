# src/baselines.py
from typing import List
import pandas as pd

TARGET = 5000


def best_ask(snapshot: pd.DataFrame) -> List[int]:
    """Send all shares to venue with best ask price"""
    ask_prices = snapshot["ask_px_00"].tolist()
    ask_sizes = snapshot["ask_sz_00"].tolist()

    if not ask_prices:
        return []

    # Find best valid ask price (where size > 0)
    valid_venues = [(i, price) for i, (price, size) in enumerate(zip(ask_prices, ask_sizes)) if size > 0]
    if not valid_venues:
        return [0] * len(ask_prices)

    idx = min(valid_venues, key=lambda x: x[1])[0]
    alloc = [0] * len(ask_prices)
    alloc[idx] = TARGET
    return alloc


def vwap(snapshot: pd.DataFrame) -> List[int]:
    """Allocate proportionally to displayed size (VWAP)"""
    ask_sizes = snapshot["ask_sz_00"].tolist()
    ask_prices = snapshot["ask_px_00"].tolist()

    if not ask_sizes:
        return []

    # Filter out venues with zero size
    valid_venues = [(i, size) for i, size in enumerate(ask_sizes) if size > 0]
    total_size = sum([v[1] for v in valid_venues])

    if total_size == 0:
        # Fallback to equal split
        n = len(ask_sizes)
        if n == 0:
            return []
        base = TARGET // n
        alloc = [base] * n
        for i in range(TARGET - base * n):
            alloc[i] += 1
        return alloc

    # Proportional allocation
    alloc = [0] * len(ask_sizes)
    allocated = 0

    for i, size in valid_venues[:-1]:  # All but last
        share = int(round(TARGET * size / total_size))
        alloc[i] = share
        allocated += share

    # Last venue gets remainder
    if valid_venues:
        last_idx = valid_venues[-1][0]
        alloc[last_idx] = TARGET - allocated

    return alloc


def twap_60s(snapshot: pd.DataFrame, shares_this_snap: int) -> List[int]:
    """Allocate shares for this specific snapshot in TWAP strategy"""
    if shares_this_snap == 0:
        return [0] * len(snapshot)

    # Use VWAP logic for this time slice
    ask_sizes = snapshot["ask_sz_00"].tolist()
    if not ask_sizes:
        return []

    # Filter out venues with zero size
    valid_venues = [(i, size) for i, size in enumerate(ask_sizes) if size > 0]
    total_size = sum([v[1] for v in valid_venues])

    if total_size == 0:
        # Fallback to cheapest venue
        ask_prices = snapshot["ask_px_00"].tolist()
        idx = ask_prices.index(min(ask_prices))
        alloc = [0] * len(ask_prices)
        alloc[idx] = shares_this_snap
        return alloc

    # Proportional allocation
    alloc = [0] * len(ask_sizes)
    allocated = 0

    for i, size in valid_venues[:-1]:  # All but last
        share = int(round(shares_this_snap * size / total_size))
        alloc[i] = share
        allocated += share

    # Last venue gets remainder
    if valid_venues:
        last_idx = valid_venues[-1][0]
        alloc[last_idx] = shares_this_snap - allocated

    return alloc