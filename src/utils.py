from typing import List
import pandas as pd

def load_snapshots(path: str) -> List[pd.DataFrame]:
    """
    Load L1 data from CSV, drop duplicates per timestamp & venue,
    then return a list of snapshots (one DataFrame per unique ts_event).
    """
    df = pd.read_csv(path)
    df = df.sort_values("ts_event")
    # keep first update per (timestamp, publisher_id)
    df = df.drop_duplicates(subset=["ts_event", "publisher_id"], keep="first")
    # group into snapshots by ts_event
    snapshots = [group.reset_index(drop=True)
                 for _, group in df.groupby("ts_event")]
    return snapshots
