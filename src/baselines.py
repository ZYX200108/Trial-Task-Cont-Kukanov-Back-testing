from typing import List
import pandas as pd

TARGET = 5000

def best_ask(snapshot: pd.DataFrame) -> List[int]:
    asks = snapshot["ask_px_00"].tolist()
    idx  = asks.index(min(asks))
    alloc = [0]*len(asks)
    alloc[idx] = TARGET
    return alloc

def vwap(snapshot: pd.DataFrame) -> List[int]:
    sizes = snapshot["ask_sz_00"].tolist()
    total = sum(sizes)
    if total == 0:
        # equal‐split fallback
        n = len(sizes)
        base = TARGET//n
        alloc = [base]*n
        for i in range(TARGET - base*n):
            alloc[i] += 1
        return alloc

    alloc = [int(round(TARGET * s/total)) for s in sizes]
    diff  = TARGET - sum(alloc)
    # correct rounding by placing remainder at cheapest venue
    asks = snapshot["ask_px_00"].tolist()
    idx  = asks.index(min(asks))
    alloc[idx] += diff
    return alloc

def twap_equal(snapshot: pd.DataFrame,
               remain_snaps: int,
               remain_shares: int) -> List[int]:
    share_per = remain_shares/remain_snaps
    sizes     = snapshot["ask_sz_00"].tolist()
    total     = sum(sizes)
    if total == 0:
        n = len(sizes)
        base = int(round(share_per/n))
        return [base]*n
    return [int(round(share_per * s/total)) for s in sizes]
