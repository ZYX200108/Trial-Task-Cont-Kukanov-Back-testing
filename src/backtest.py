# src/backtest.py
import argparse
import json
from src.utils import load_snapshots
from src.allocator import allocate, TARGET
from src.baselines import best_ask, vwap, twap_60s


def simulate_static_execution(snapshots, params: dict) -> dict:
    """
    Simulate execution using static allocation
    """
    if not snapshots:
        return {"cash": 0.0, "avg_price": 0.0, "filled": 0}

    # Get allocation from first snapshot
    alloc = allocate(snapshots[0], params)

    # Execute the allocation across all snapshots
    remaining = alloc.copy()
    cash_spent = 0.0
    filled = 0

    for snap in snapshots:
        if sum(remaining) == 0:
            break

        ask_prices = snap["ask_px_00"].tolist()
        ask_sizes = snap["ask_sz_00"].tolist()

        # Execute what we can at this snapshot
        for i in range(len(remaining)):
            if remaining[i] > 0 and i < len(ask_sizes) and i < len(ask_prices):
                exe = min(remaining[i], ask_sizes[i])
                if exe > 0:
                    cash_spent += exe * ask_prices[i]
                    filled += exe
                    remaining[i] -= exe

    # Handle any remaining unfilled quantity at the end
    unfilled = TARGET - filled
    if unfilled > 0 and snapshots:
        # Market order at the end to complete the trade
        last_snap = snapshots[-1]
        last_prices = last_snap["ask_px_00"].tolist()
        if last_prices:
            cheapest_price = min(last_prices)
            cash_spent += unfilled * cheapest_price
            filled += unfilled

    avg_price = cash_spent / filled if filled > 0 else 0.0

    return {
        "cash": cash_spent,
        "avg_price": avg_price,
        "filled": filled
    }


def simulate_dynamic(snapshots, strategy, strategy_name="") -> dict:
    """Simulate dynamic execution strategies (baselines)"""
    remaining = TARGET
    cash = 0.0
    filled = 0

    for i, snap in enumerate(snapshots):
        if remaining <= 0:
            break

        if strategy_name == "twap_60s":
            # TWAP: divide equally across 60-second buckets
            # Assuming snapshots are roughly 1 per second
            bucket_size = 60
            bucket_idx = i // bucket_size
            total_buckets = max(1, len(snapshots) // bucket_size)

            # Execute only at the start of each bucket
            if i % bucket_size == 0:
                shares_per_bucket = remaining // max(1, total_buckets - bucket_idx)
                alloc = strategy(snap, shares_per_bucket)
            else:
                alloc = [0] * len(snap)
        else:
            alloc = strategy(snap)

        ask_prices = snap["ask_px_00"].tolist()
        ask_sizes = snap["ask_sz_00"].tolist()

        # Execute the allocation
        for j in range(min(len(alloc), len(ask_sizes), len(ask_prices))):
            if alloc[j] > 0:
                exe = min(alloc[j], ask_sizes[j], remaining)
                if exe > 0:
                    cash += exe * ask_prices[j]
                    filled += exe
                    remaining -= exe

    # Ensure we fill the entire order
    if remaining > 0 and snapshots:
        last_prices = snapshots[-1]["ask_px_00"].tolist()
        if last_prices:
            cheapest_price = min(last_prices)
            cash += remaining * cheapest_price
            filled += remaining

    avg_price = cash / filled if filled > 0 else 0.0
    return {"cash": cash, "avg_price": avg_price, "filled": filled}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    # Load snapshots
    snapshots = load_snapshots(args.data)

    # Parameter search grid
    param_grid = [
        {"lambda_under": lu, "lambda_over": lo, "theta_queue": tq}
        for lu in [0.0, 0.5, 1.0, 2.0]  # Underfill penalty
        for lo in [0.0]  # Overfill penalty (keeping at 0)
        for tq in [0.0, 0.02, 0.05, 0.1]  # Queue risk penalty
    ]

    # Find best parameters
    best_result = None
    best_params = None
    best_avg_price = float("inf")

    for params in param_grid:
        result = simulate_static_execution(snapshots, params)
        # Only consider results that filled exactly TARGET
        if result["filled"] == TARGET and result["avg_price"] < best_avg_price:
            best_avg_price = result["avg_price"]
            best_result = result
            best_params = params

    # Run baselines
    baseline_best = simulate_dynamic(snapshots, best_ask)
    baseline_vwap = simulate_dynamic(snapshots, vwap)
    baseline_twap = simulate_dynamic(snapshots, lambda s, shares: twap_60s(s, shares), "twap_60s")

    # Calculate savings
    def calc_bps(ref, test):
        if ref["filled"] == 0 or test["filled"] == 0:
            return 0.0
        return ((ref["avg_price"] - test["avg_price"]) / ref["avg_price"]) * 10000

    output = {
        "best_params": best_params,
        "router": best_result,
        "baselines": {
            "best_ask": baseline_best,
            "vwap": baseline_vwap,
            "twap_60s": baseline_twap
        },
        "savings_bps": {
            "vs_best_ask": calc_bps(baseline_best, best_result),
            "vs_vwap": calc_bps(baseline_vwap, best_result),
            "vs_twap": calc_bps(baseline_twap, best_result)
        }
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()