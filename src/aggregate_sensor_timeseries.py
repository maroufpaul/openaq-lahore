import os
import re
import pandas as pd


# paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SENSORS_DIR = os.path.join(DATA_DIR, "sensors")
RAW_DIR = os.path.join(SENSORS_DIR, "raw")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

META_FILE = os.path.join(OUTPUT_DIR, "sensors_lahore_joined.csv")


# helper: fall back to filename if CSV doesn't have sensor_id
# e.g. sensor_25135_days3000.csv -> 25135
FNAME_ID_RE = re.compile(r"(\d+)")


def sensor_id_from_filename(fname: str):
    m = FNAME_ID_RE.search(fname)
    if m:
        return int(m.group(1))
    return None


#  walk raw/ and aggregate
records = []

for fname in os.listdir(RAW_DIR):
    if not fname.lower().endswith(".csv"):
        continue

    fpath = os.path.join(RAW_DIR, fname)
    print(f"➡️ reading {fname} ...")

    try:
        df = pd.read_csv(fpath)
    except Exception as e:
        print(f"   ⚠️ failed to read {fname}: {e}")
        continue

    # guess sensor_id
    if "sensor_id" in df.columns:
        sid = df["sensor_id"].iloc[0]
    else:
        sid = sensor_id_from_filename(fname)

    if pd.isna(sid):
        print(f"   ⚠️ no sensor_id in file or name for {fname}, skipping")
        continue

    # figure out the value column
    value_col = None
    for cand in ["value", "pm25", "pm_2_5", "pm2_5", "concentration"]:
        if cand in df.columns:
            value_col = cand
            break

    if value_col is None:
        print(f"   ⚠️ {fname} has no value column, skipping")
        continue

    # drop NaNs
    vals = df[value_col].dropna()
    if len(vals) == 0:
        print(f"   ⚠️ {fname} has no numeric values, skipping")
        continue

    pm_mean = float(vals.mean())
    pm_median = float(vals.median())
    pm_max = float(vals.max())
    n_obs = int(len(vals))

    # if there's a datetime, we can store min/max
    if "date" in df.columns:
        tmin = df["date"].min()
        tmax = df["date"].max()
    elif "datetime" in df.columns:
        tmin = df["datetime"].min()
        tmax = df["datetime"].max()
    else:
        tmin = None
        tmax = None

    records.append(
        {
            "sensor_id": int(sid),
            "pm25_mean": pm_mean,
            "pm25_median": pm_median,
            "pm25_max": pm_max,
            "n_obs": n_obs,
            "ts_start": tmin,
            "ts_end": tmax,
            "source_file": fname,
        }
    )

# to df
agg_df = pd.DataFrame(records)
print("\n✅ aggregated sensors:", len(agg_df))

agg_out = os.path.join(OUTPUT_DIR, "sensor_timeseries_aggregated.csv")
agg_df.to_csv(agg_out, index=False)
print("✅ wrote", agg_out)


#  join with metadata (coords + names)

meta_df = pd.read_csv(META_FILE)

merged = meta_df.merge(agg_df, on="sensor_id", how="left")

final_out = os.path.join(OUTPUT_DIR, "sensors_lahore_with_pm25.csv")
merged.to_csv(final_out, index=False)
print("✅ wrote", final_out)


# optional: GeoPackage for QGIS

try:
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        merged,
        geometry=[Point(xy) for xy in zip(merged["longitude"], merged["latitude"])],
        crs="EPSG:4326",
    )

    gpkg_out = os.path.join(OUTPUT_DIR, "sensors_lahore_with_pm25.gpkg")
    gdf.to_file(gpkg_out, driver="GPKG", layer="sensors_pm25")
    print("✅ wrote", gpkg_out)
except Exception as e:
    print("⚠️ could not write GeoPackage (geopandas not installed?):", e)
