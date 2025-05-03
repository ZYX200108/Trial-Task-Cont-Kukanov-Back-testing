from typing import List
import pandas as pd

TARGET = 5000

def best_ask(snapshot: pd.DataFrame) -> List[int]:
    asks = snapshot["ask_px_00"].tolist()
    idx  = asks.index(min(asks))
    alloc = [0] * len(asks)
    alloc[idx] = TARGET
    return alloc

def vwap(snapshot: pd.DataFrame) -> List[int]:
    sizes = snapshot["ask_sz_00"].tolist()
    total = sum(sizes)
    if total == 0:
        n = len(sizes)
        base = TARGET // n
        alloc = [base] * n
        for i in range(TARGET - base * n):
            alloc[i] += 1
        return alloc

    alloc = [int(round(TARGET * sz / total)) for sz in sizes]
    diff = TARGET - sum(alloc)
    asks = snapshot["ask_px_00"].tolist()
    idx = asks.index(min(asks))
    alloc[idx] += diff
    return alloc

def twap_equal(snapshot: pd.DataFrame,
               remaining_snapshots: int,
               remaining_shares: int) -> List[int]:
    share_per_snap = remaining_shares / remaining_snapshots
    sizes = snapshot["ask_sz_00"].tolist()
    total = sum(sizes)
    if total == 0:
        n = len(sizes)
        base = int(round(share_per_snap / n))
        return [base] * n

    return [int(round(share_per_snap * sz / total)) for sz in sizes]
