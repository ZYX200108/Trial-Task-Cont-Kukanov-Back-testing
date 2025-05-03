# from typing import List
# import pandas as pd
#
# def load_snapshots(path: str) -> List[pd.DataFrame]:
#     """
#     Load L1 feed from CSV, dedupe per (ts_event, publisher_id),
#     and return snapshots in time order.
#     """
#     df = pd.read_csv(path)
#     df = df.sort_values("ts_event")
#     df = df.drop_duplicates(subset=["ts_event", "publisher_id"], keep="first")
#     return [group.reset_index(drop=True)
#             for _, group in df.groupby("ts_event")]

# utils.py (revised)
from typing import List
import pandas as pd


def process_l1_data(df):
    """Convert raw L1 feed into order book snapshots with state carry-forward"""
    df = df.sort_values('sequence')
    snapshots = []
    current_order_book = None

    for _, row in df.iterrows():
        # Initialize or update order book
        if current_order_book is None:
            # First row: create template with NaN prices and zero sizes
            current_order_book = {
                **{f"bid_px_{i:02d}": None for i in range(10)},
                **{f"bid_sz_{i:02d}": 0 for i in range(10)},
                **{f"ask_px_{i:02d}": None for i in range(10)},
                **{f"ask_sz_{i:02d}": 0 for i in range(10)}
            }

        # Update current order book
        depth = row['depth']
        if depth < 10:
            if row['side'] == 'B':
                current_order_book[f'bid_px_{depth:02d}'] = row[f'bid_px_{depth:02d}']
                current_order_book[f'bid_sz_{depth:02d}'] = row[f'bid_sz_{depth:02d}']
            elif row['side'] == 'A':
                current_order_book[f'ask_px_{depth:02d}'] = row[f'ask_px_{depth:02d}']
                current_order_book[f'ask_sz_{depth:02d}'] = row[f'ask_sz_{depth:02d}']

        # Create snapshot at ts_event boundaries
        if not snapshots or snapshots[-1]['ts_event'].iloc[0] != row['ts_event']:
            snap = pd.DataFrame([current_order_book.copy()])
            snap['ts_event'] = row['ts_event']
            snapshots.append(snap)

    return snapshots


def load_snapshots(path: str) -> List[pd.DataFrame]:
    """Load and process L1 data with state tracking"""
    df = pd.read_csv(
        path,
        dtype={'depth': 'int8', 'sequence': 'int64'},
        parse_dates=['ts_event']
    )
    return process_l1_data(df)