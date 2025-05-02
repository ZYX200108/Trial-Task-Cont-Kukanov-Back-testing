from typing import List
import pandas as pd

TARGET = 5000

def best_ask(snapshot: pd.DataFrame) -> List[int]:
    """
    Send entire slice to the single lowest ask price.
    """
    asks = snapshot["ask_px_00"].tolist()
    idx = asks.index(min(asks))
    alloc = [0] * len(asks)
    alloc[idx] = TARGET
    return alloc

def vwap(snapshot: pd.DataFrame) -> List[int]:
    """
    Split in proportion to displayed size at each venue.
    """
    sizes = snapshot["ask_sz_00"].tolist()
    total = sum(sizes)
    if total == 0:
        # equal split if no size info
        n = len(sizes)
        base = TARGET // n
        alloc = [base] * n
        for i in range(TARGET - base * n):
            alloc[i] += 1
        return alloc

    # round each piece, then adjust any rounding error on best ask
    alloc = [int(round(TARGET * sz / total)) for sz in sizes]
    diff = TARGET - sum(alloc)
    asks = snapshot["ask_px_00"].tolist()
    idx = asks.index(min(asks))
    alloc[idx] += diff
    return alloc

def twap_equal(snapshot: pd.DataFrame,
               remaining_snapshots: int,
               remaining_shares: int) -> List[int]:
    """
    At each step, trade an equal share of what's left,
    then split that share by displayed size weights.
    """
    # shares to trade this snapshot
    share_per_snap = remaining_shares / remaining_snapshots
    sizes = snapshot["ask_sz_00"].tolist()
    total = sum(sizes)
    if total == 0:
        # fallback: equal across venues
        n = len(sizes)
        base = int(round(share_per_snap / n))
        return [base] * n

    alloc = [int(round(share_per_snap * sz / total)) for sz in sizes]
    return alloc
