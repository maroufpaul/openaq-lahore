# src/prepare_sensors.py

import os
import pandas as pd

# paths (relative to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SENSORS_DIR = os.path.join(DATA_DIR, "sensors")
BOUNDARY_DIR = os.path.join(DATA_DIR, "boundary")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

PM25_FILE = os.path.join(SENSORS_DIR, "lahore_pm25_sensors_subset.xlsx")
LOC_FILE = os.path.join(SENSORS_DIR, "lahore_locations_subset.xlsx")


# load both tables
pm25_df = pd.read_excel(PM25_FILE)
loc_df = pd.read_excel(LOC_FILE)

# quick sanity print
print("PM25 rows:", len(pm25_df))
print("Locations rows:", len(loc_df))
print("PM25 columns:", list(pm25_df.columns))
print("Location columns:", list(loc_df.columns))

# join on locations_id
# in both files the key is called 'locations_id'
merged = pm25_df.merge(
    loc_df,
    on="locations_id",
    how="left",
    suffixes=("_pm", "_loc"),
)


# pick the coordinate columns
# ----------------------------------------
# from  sample, locations file has: lat, lon
# pm25 file had: lat_x, lon_x, lat_y, lon_y
# We'll trust the locations file (usually cleaner)
if "lat" in merged.columns and "lon" in merged.columns:
    merged["latitude"] = merged["lat"]
    merged["longitude"] = merged["lon"]
else:
    # fallback to pm25 columns if for some reason lat/lon are missing
    merged["latitude"] = merged["lat_x"]
    merged["longitude"] = merged["lon_x"]


# drop sensors that have no coordinates
before = len(merged)
merged = merged.dropna(subset=["latitude", "longitude"])
after = len(merged)
print(f"Dropped {before - after} sensors without coordinates.")

# create a nice output subset
keep_cols = [
    "sensor_id",
    "sensor_name",
    "parameter_name",
    "locations_id",
    "name",              # location name
    "owner_name",
    "latitude",
    "longitude",
    "datetimeFirst_utc",
    "datetimeLast_utc",
]
# keep only existing ones
keep_cols = [c for c in keep_cols if c in merged.columns]

clean = merged[keep_cols].copy()


# save to CSV (always works)
sensors_csv = os.path.join(OUTPUT_DIR, "sensors_lahore_joined.csv")
clean.to_csv(sensors_csv, index=False, encoding="utf-8")
print("✅ wrote", sensors_csv)

#
# optional: save to GeoPackage if geopandas is installed
# ----------------------------------------
try:
    import geopandas as gpd
    from shapely.geometry import Point

    gdf = gpd.GeoDataFrame(
        clean,
        geometry=[Point(xy) for xy in zip(clean["longitude"], clean["latitude"])],
        crs="EPSG:4326",
    )

    sensors_gpkg = os.path.join(OUTPUT_DIR, "sensors_lahore_joined.gpkg")
    gdf.to_file(sensors_gpkg, driver="GPKG", layer="sensors_lahore")
    print("✅ wrote", sensors_gpkg)

except Exception as e:
    print("⚠️ geopandas not available, skipped GeoPackage export.")
    print("reason:", e)
