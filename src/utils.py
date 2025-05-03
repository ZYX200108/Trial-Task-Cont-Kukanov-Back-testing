# src/utils.py
from typing import List
import pandas as pd


def load_snapshots(path: str) -> List[pd.DataFrame]:
    """
    Load L1 data and create proper snapshots per timestamp
    """
    df = pd.read_csv(path)

    # Keep only first message per publisher per timestamp
    df = df.sort_values(['ts_event', 'publisher_id'])
    df = df.drop_duplicates(subset=['ts_event', 'publisher_id'], keep='first')

    # Group by timestamp to create snapshots
    snapshots = []
    for ts_event, group in df.groupby('ts_event'):
        snapshot = group.copy()
        # Ensure we have ask data
        if 'ask_px_00' in snapshot.columns and len(snapshot) > 0:
            snapshots.append(snapshot.reset_index(drop=True))

    return snapshots