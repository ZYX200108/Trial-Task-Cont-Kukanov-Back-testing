import argparse
import json

from src.utils     import load_snapshots
from src.allocator import allocate
from src.baselines import best_ask, vwap, twap_equal

TARGET = 5000

def simulate_static(snapshots, params):
    # 1) allocate once on first snapshot
    X_star = allocate(snapshots[0], params)

    # per-venue remaining wants
    rem = X_star.copy()
    cash_spent = 0.0

    # 2) walk through snapshots
    for snap in snapshots:
        if sum(rem) <= 0:
            break
        fills = []
        for k, want in enumerate(rem):
            can = min(want, snap["ask_sz_00"].iloc[k])
            fills.append(can)
            rem[k] -= can
        cash_spent += sum(f * p
                          for f, p in zip(fills, snap["ask_px_00"]))
    # 3) final market order for any leftover
    leftover = sum(rem)
    if leftover > 0:
        last_asks = snapshots[-1]["ask_px_00"].tolist()
        best     = min(last_asks)
        cash_spent += leftover * best

    avg_price = cash_spent / TARGET
    return {"cash": cash_spent, "avg_price": avg_price}


def simulate_dynamic(snapshots, strategy, **kwargs):
    remaining = TARGET
    cash_spent = 0.0
    n_snap = len(snapshots)

    for i, snap in enumerate(snapshots, start=1):
        if remaining <= 0:
            break
        if strategy is best_ask:
            alloc = best_ask(snap)
        elif strategy is vwap:
            alloc = vwap(snap)
        elif strategy is twap_equal:
            alloc = twap_equal(snap, n_snap - i + 1, remaining)
        else:
            alloc = allocate(snap, kwargs)

        fills = [min(a, s)
                 for a, s in zip(alloc, snap["ask_sz_00"])]
        cash_spent += sum(f * p
                          for f, p in zip(fills, snap["ask_px_00"]))
        remaining -= sum(fills)

    if remaining > 0:
        last_asks = snapshots[-1]["ask_px_00"].tolist()
        best     = min(last_asks)
        cash_spent += remaining * best

    avg_price = cash_spent / (TARGET if remaining <= 0 else TARGET)
    return {"cash": cash_spent, "avg_price": avg_price}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True,
                        help="Path to l1_day.csv")
    args = parser.parse_args()

    snaps = load_snapshots(args.data)

    # grid search
    lambdas = [50, 100, 200]
    thetas  = [10, 50]
    best    = {"params": None, "res": None, "avg": float("inf")}

    for lu in lambdas:
        for lo in lambdas:
            for tq in thetas:
                p = {"lambda_under": lu,
                     "lambda_over":  lo,
                     "theta_queue":  tq}
                out = simulate_static(snaps, p)
                if out["avg_price"] < best["avg"]:
                    best = {"params": p, "res": out, "avg": out["avg_price"]}

    # baselines (dynamic)
    res_best = simulate_dynamic(snaps, best_ask)
    res_vwap = simulate_dynamic(snaps, vwap)
    res_twap = simulate_dynamic(snaps, twap_equal)

    # compile JSON
    out = {
        "best_params": best["params"],
        "router":      best["res"],
        "best_ask":    res_best,
        "vwap":        res_vwap,
        "twap_60s":    res_twap,
        "savings_bps": {
            "vs_best_ask": (res_best["avg_price"] - best["res"]["avg_price"])
                             / res_best["avg_price"] * 1e4,
            "vs_vwap":     (res_vwap["avg_price"] - best["res"]["avg_price"])
                             / res_vwap["avg_price"] * 1e4,
            "vs_twap":     (res_twap["avg_price"] - best["res"]["avg_price"])
                             / res_twap["avg_price"] * 1e4
        }
    }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
