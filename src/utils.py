# src/utils.py - Correct implementation
from typing import List
import pandas as pd


def load_snapshots(path: str) -> List[pd.DataFrame]:
    """
    Load L1 data and create proper multi-venue snapshots
    """
    df = pd.read_csv(path)

    # Sort by time and publisher
    df = df.sort_values(['ts_event', 'publisher_id'])

    # Drop duplicates to keep only first update per publisher per timestamp
    df = df.drop_duplicates(subset=['ts_event', 'publisher_id'], keep='first')

    # Group by timestamp to create snapshots
    snapshots = []

    for ts_event, group in df.groupby('ts_event'):
        # Keep only rows with valid ask data
        valid_group = group[group['ask_px_00'].notna() & (group['ask_sz_00'] > 0)]

        if len(valid_group) > 0:
            # Ensure publisher_id is maintained for venue identification
            snapshot = valid_group[['publisher_id', 'ask_px_00', 'ask_sz_00']].copy()
            snapshot = snapshot.reset_index(drop=True)
            snapshots.append(snapshot)

    # Debug info
    # venue_counts = [len(snap) for snap in snapshots]
    # print(f"Loaded {len(snapshots)} snapshots")
    # print(f"Average venues per snapshot: {sum(venue_counts) / len(venue_counts):.2f}")
    # print(f"Max venues in a snapshot: {max(venue_counts)}")

    # Find and use a snapshot with multiple venues for testing
    # multi_venue_snapshots = [i for i, snap in enumerate(snapshots) if len(snap) > 1]
    # if multi_venue_snapshots:
    #     print(f"Found {len(multi_venue_snapshots)} snapshots with multiple venues")

    return snapshots