# Smart Order Router – Cont & Kukanov Static Model

## Overview
This project implements a Smart Order Router based on the static cost model introduced by Cont & Kukanov in their paper "Optimal Order Placement in Limit Order Markets". The router optimally splits a 5,000-share buy order across multiple venues while minimizing total execution cost including market impact and execution risk penalties.

## Code Structure

### Core Components
- `src/allocator.py`: Implements the exact algorithm from `allocator_pseudocode.txt`
  - `allocate()`: Main allocation function that generates all possible order splits
  - `compute_cost()`: Calculates total cost including penalties for each allocation
- `src/backtest.py`: Main execution loop and parameter optimization
  - `simulate_static_execution()`: Executes the optimal allocation across snapshots
  - `simulate_dynamic()`: Runs baseline strategies for comparison
- `src/baselines.py`: Three baseline strategies
  - `best_ask()`: Naive strategy sending all orders to cheapest venue
  - `vwap()`: Volume-weighted allocation across venues
  - `twap_60s()`: Time-weighted average price in 60-second buckets
- `src/utils.py`: Data loading and snapshot creation from L1 market data

### Execution Flow
1. Load L1 market data and create venue snapshots
2. Generate parameter grid for λ_under, λ_over, and θ_queue
3. Find optimal parameters by minimizing average execution price
4. Compare against baseline strategies
5. Output results in JSON format

## Parameter Search Strategy

The parameter search uses a grid search approach with values scaled relative to stock price (~$223):

- **λ_under** (underfill penalty): [0%, 0.1%, 0.5%, 1%, 2%, 5%, 10%] of stock price
- **λ_over** (overfill penalty): [0%, 0.05%, 0.1%, 0.5%] of stock price  
- **θ_queue** (queue risk penalty): [0%, 0.01%, 0.05%, 0.1%, 0.5%, 1%] of stock price

This scaling ensures penalties are meaningful relative to the ~$1.1M total order value.

## Improvement Idea: Queue Position Modeling

The current implementation could be enhanced by modeling queue position more realistically. Instead of assuming immediate execution at the best ask, we could:

1. Track queue depth at each venue and estimate our position
2. Model order cancellations and new arrivals that affect queue position
3. Use historical fill rates to estimate execution probability
4. Incorporate time-to-fill estimates in the cost function

This would better capture the execution risk of limit orders placed deeper in the queue, leading to more realistic allocation decisions between aggressive (immediate execution) and passive (queue-based) strategies.

## Usage

```bash
python -m src.backtest --data data/l1_day.csv > results.json
