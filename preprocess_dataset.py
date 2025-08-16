 # preprocess_dataset.py
import pandas as pd
import json
from pathlib import Path

DATA_PATH = Path("data/activities.csv")
OUT_PATH = Path("data/context_summary.json")

# Update these columns to match your CSV column names if different
COL_TIME = "Start time"       # timestamp column name
COL_LOCATION = "Location"
COL_TIME_OF_DAY = "Time of a day"   # Morning/Afternoon/Evening/Night if available
COL_OBJECT = "Object"
COL_POSTURE = "Posture"

def is_night_hour(hour):
    return hour >= 22 or hour < 6

def main():
    if not DATA_PATH.exists():
        print("Put your CSV at:", DATA_PATH)
        return

    df = pd.read_csv(DATA_PATH)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    
    # Print debug info
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    print(f"Unique locations: {df[COL_LOCATION].unique()}")

    # Ensure timestamp parsing
    if COL_TIME in df.columns:
        df[COL_TIME] = pd.to_datetime(df[COL_TIME], format='%I:%M:%S %p', errors="coerce")

    # Prepare summary dict
    summary = {
        "total_events": len(df),
        "locations": {},
        "door_night_pct": {},  # per-location percent of door events at night
        "posture_stats": {}    # per-location posture distributions
    }

    # FIX 1: Add the missing locations count
    location_counts = df[COL_LOCATION].value_counts().to_dict()
    # Convert to lowercase keys for consistency
    summary["locations"] = {str(k).lower(): v for k, v in location_counts.items()}

    # compute door/night percentages per location
    door_mask = df[COL_OBJECT].astype(str).str.lower().str.contains("door", na=False)
    door_df = df[door_mask].copy()
    if COL_TIME in df.columns:
        door_df["hour"] = door_df[COL_TIME].dt.hour

    for loc, sub in door_df.groupby(COL_LOCATION):
        total = len(sub)
        if total == 0:
            pct = 0.0
        else:
            if "hour" in sub.columns:
                night_cnt = sub[sub["hour"].apply(lambda h: is_night_hour(h) if pd.notnull(h) else False)].shape[0]
            else:
                # fallback to Time of a day column
                night_cnt = sub[sub[COL_TIME_OF_DAY].astype(str).str.lower().str.contains("night", na=False)].shape[0]
            pct = night_cnt / total
        summary["door_night_pct"][str(loc).lower()] = pct

    # posture stats
    for loc, sub in df.groupby(COL_LOCATION):
        posture_counts = sub[COL_POSTURE].fillna("unknown").astype(str).str.lower().value_counts(normalize=True).to_dict()
        summary["posture_stats"][str(loc).lower()] = posture_counts

    # basic overall heuristics
    summary["heuristics"] = {
        "door_night_threshold_require_confirm": 0.15,  # if door rarely used at night, require confirmation at night
        "thermostat_max_delta": 5.0,  # degrees Celsius without confirmation
    }

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    print("Wrote context summary to:", OUT_PATH)
    
    # Print summary for verification
    print(f"\nSummary:")
    print(f"Total events: {summary['total_events']}")
    print(f"Locations found: {len(summary['locations'])}")
    print(f"Location counts: {summary['locations']}")

if __name__ == "__main__":
    main()