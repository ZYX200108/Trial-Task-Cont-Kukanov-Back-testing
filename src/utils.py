from typing import List
import pandas as pd

def load_snapshots(path: str) -> List[pd.DataFrame]:
    """
    Load L1 data from CSV, drop duplicates per timestamp & venue,
    then group into a list of snapshots (one DataFrame per unique ts_event).
    """
    df = pd.read_csv(path)
    df = df.sort_values("ts_event")
    # keep first update per (timestamp, publisher)
    df = df.drop_duplicates(subset=["ts_event", "publisher_id"], keep="first")
    # group all rows with the same ts_event into one snapshot
    snapshots = [group for _, group in df.groupby("ts_event")]
    return snapshots
