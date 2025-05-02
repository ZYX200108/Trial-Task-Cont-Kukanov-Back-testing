import argparse
import json

from src.utils      import load_snapshots
from src.allocator  import allocate
from src.baselines  import best_ask, vwap, twap_equal

TARGET = 5000

def simulate(snapshots, strategy, params=None):
    remaining = TARGET
    cash_spent = 0.0
    n_snap = len(snapshots)

    for i, snapshot in enumerate(snapshots, start=1):
        if remaining <= 0:
            break

        if strategy == best_ask:
            alloc = best_ask(snapshot)
        elif strategy == vwap:
            alloc = vwap(snapshot)
        elif strategy == twap_equal:
            alloc = twap_equal(snapshot, n_snap - i + 1, remaining)
        else:
            alloc = allocate(snapshot, params)

        # execute up to displayed size
        fills = [
            min(a, sz)
            for a, sz in zip(alloc, snapshot["ask_sz_00"])
        ]
        cash_spent += sum(f * p
                          for f, p in zip(fills, snapshot["ask_px_00"]))
        remaining  -= sum(fills)

    filled = TARGET - max(0, remaining)
    avg_price = cash_spent / filled if filled > 0 else None

    return {"cash": cash_spent, "avg_price": avg_price}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True,
                        help="Path to l1_day.csv")
    args = parser.parse_args()

    snapshots = load_snapshots(args.data)

    # 1) Grid search for static router
    lambdas = [0.0, 0.1, 0.5, 1.0]
    thetas  = [0.0, 0.1]
    best    = {"params": None, "result": None, "avg": float("inf")}

    for lu in lambdas:
        for lo in lambdas:
            for tq in thetas:
                p = {"lambda_under": lu,
                     "lambda_over":  lo,
                     "theta_queue":  tq}
                out = simulate(snapshots, strategy=None, params=p)
                if out["avg_price"] is not None and out["avg_price"] < best["avg"]:
                    best = {"params": p, "result": out,
                            "avg": out["avg_price"]}

    # 2) Baselines
    res_best = simulate(snapshots, best_ask)
    res_vwap = simulate(snapshots, vwap)
    res_twap = simulate(snapshots, twap_equal)

    # 3) Compile output
    output = {
      "best_params": best["params"],
      "router":      best["result"],
      "best_ask":    res_best,
      "vwap":        res_vwap,
      "twap_60s":    res_twap,
      "savings_bps": {
        "vs_best_ask": (res_best["avg_price"] - best["result"]["avg_price"]) * 1e4,
        "vs_vwap":     (res_vwap["avg_price"] - best["result"]["avg_price"]) * 1e4,
        "vs_twap":     (res_twap["avg_price"] - best["result"]["avg_price"]) * 1e4
      }
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
