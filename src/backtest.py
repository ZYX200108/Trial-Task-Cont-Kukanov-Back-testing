import argparse
import json
from src.utils import load_snapshots
from src.allocator import allocate, TARGET
from src.baselines import best_ask, vwap, twap_equal


def simulate_execution(snapshots, alloc: list) -> dict:
    rem = alloc.copy()
    cash = 0.0
    filled = 0

    for snap in snapshots:
        if sum(rem) == 0:
            break
        depths = snap["ask_sz_00"].tolist()
        # prices = snap["ask_px_00"].tolist()
        prices = snap["ask_px_00"].fillna(method='ffill').tolist()

        # Calculate fills without exceeding remaining shares
        fills = []
        remaining = sum(rem)
        for r, d in zip(rem, depths):
            fill = min(r, d)
            if remaining <= 0:
                fills.append(0)
            else:
                fill = min(fill, remaining)
                fills.append(fill)
                remaining -= fill

        cash += sum(f * p for f, p in zip(fills, prices))
        rem = [r - f for r, f in zip(rem, fills)]
        filled += sum(fills)

    # Final market order for leftovers
    remaining = sum(rem)
    if remaining > 0 and snapshots:
        last_prices = snapshots[-1]["ask_px_00"].tolist()
        cash += remaining * min(last_prices)
        filled += remaining

    avg_price = cash / filled if filled > 0 else 0.0
    return {"cash": cash, "avg_price": avg_price, "filled": filled}


def simulate_dynamic(snapshots, strategy):
    rem = TARGET
    cash = 0.0
    filled = 0
    n = len(snapshots)

    for i, snap in enumerate(snapshots):
        if rem <= 0:
            break

        if strategy == twap_equal:
            alloc = twap_equal(snap, n - i, rem)
        else:
            alloc = strategy(snap)

        depths = snap["ask_sz_00"].tolist()
        prices = snap["ask_px_00"].tolist()

        # Calculate fills without exceeding remaining shares
        fills = []
        remaining = rem
        for a, d in zip(alloc, depths):
            fill = min(a, d, remaining)
            fills.append(fill)
            remaining -= fill
            if remaining <= 0:
                break

        cash += sum(f * p for f, p in zip(fills, prices))
        rem -= sum(fills)
        filled += sum(fills)

    # Final market order for leftovers
    if rem > 0 and snapshots:
        last_prices = snapshots[-1]["ask_px_00"].tolist()
        cash += rem * min(last_prices)
        filled += rem

    avg_price = cash / filled if filled > 0 else 0.0
    return {"cash": cash, "avg_price": avg_price, "filled": filled}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    args = p.parse_args()

    # Load and validate snapshots
    snaps = load_snapshots(args.data)
    if not snaps:
        raise ValueError("No valid snapshots loaded")

    if 'ask_px_00' not in snaps[0].columns:
        raise ValueError("Invalid snapshot format - missing L1 fields")

    # p = argparse.ArgumentParser()
    # p.add_argument("--data", required=True)
    # args = p.parse_args()
    # snaps = load_snapshots(args.data)

    # Economically meaningful parameters (basis points of ~$200 stock)
    # param_grid = [
    #     {"lambda_under": lu, "lambda_over": 0.0, "theta_queue": tq}
    #     for lu in [50.0, 100.0, 200.0]  # $0.50-$2.00 per share
    #     for tq in [10.0, 20.0]  # $0.10-$0.20 per share
    # ]
    param_grid = [
        {"lambda_under": 200, "lambda_over": 0, "theta_queue": 50},  # $2/shr underfill penalty
        {"lambda_under": 500, "lambda_over": 0, "theta_queue": 100}  # $5/shr penalty
    ]

    best = {"params": None, "res": None, "avg": float("inf")}
    for params in param_grid:
        alloc = allocate(snaps, params)
        result = simulate_execution(snaps, alloc)
        if result["filled"] == TARGET and result["avg_price"] < best["avg"]:
            best = {"params": params, "res": result, "avg": result["avg_price"]}

    # Baselines (dynamic execution)
    res_best = simulate_dynamic(snaps, best_ask)
    res_vwap = simulate_dynamic(snaps, vwap)
    res_twap = simulate_dynamic(snaps, twap_equal)

    # Calculate savings only if baselines filled completely
    def safe_bps(ref, test):
        if ref["filled"] == 0 or test["filled"] == 0:
            return 0.0
        return ((ref["avg_price"] - test["avg_price"]) / ref["avg_price"]) * 10000

    output = {
        "best_params": best["params"],
        "router": best["res"],
        "baselines": {
            "best_ask": res_best,
            "vwap": res_vwap,
            "twap_60s": res_twap
        },
        "savings_bps": {
            "vs_best_ask": safe_bps(res_best, best["res"]),
            "vs_vwap": safe_bps(res_vwap, best["res"]),
            "vs_twap": safe_bps(res_twap, best["res"])
        }
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()