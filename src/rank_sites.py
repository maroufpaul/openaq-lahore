# src/rank_sites.py
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.neighbors import NearestNeighbors

ROOT = Path(r"D:\openaq-lahore")
DATA = ROOT / "data"
OUT  = ROOT / "outputs"

BOUNDARY_FP = DATA / "boundary" / "lahore_boundary.geojson"

EXPOSURE_CANDIDATES = [
    OUT / "population_pm25_exposure.gpkg",
    DATA / "worldpop" / "population_pm25_exposure.gpkg",
]
SENSORS_FP   = OUT / "sensors_lahore_with_pm25.gpkg"
SENSORS_LAYER = "sensors_pm25"

UTM43 = "EPSG:32643"   # metric CRS for Lahore

def minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    if hi == lo:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)

def read_boundary():
    b = gpd.read_file(BOUNDARY_FP)
    if b.crs is None:
        b = b.set_crs(4326, allow_override=True)
    return b

def read_exposure():
    for fp in EXPOSURE_CANDIDATES:
        if fp.exists():
            exp = gpd.read_file(fp)
            break
    else:
        raise FileNotFoundError("population_pm25_exposure.gpkg not found in outputs/ or data/worldpop/.")

    # normalize field names
    cols_lower = {c.lower(): c for c in exp.columns}
    # rename sampled column to pm25_interp
    for cand in ("sample_1", "sample_0", "sample"):
        if cand in cols_lower:
            exp = exp.rename(columns={cols_lower[cand]: "pm25_interp"})
            break
    if "pm25_interp" not in exp.columns:
        raise ValueError("Exposure layer missing sampled PM field (SAMPLE_1/pm25_interp).")
    if "pop" not in exp.columns:
        raise ValueError("Exposure layer missing 'pop' field.")

    if exp.crs is None:
        exp = exp.set_crs(4326, allow_override=True)
    return exp

def read_sensors():
    gdf = gpd.read_file(SENSORS_FP, layer=SENSORS_LAYER)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326, allow_override=True)
    gdf = gdf[gdf.geometry.notna()].copy()
    return gdf

def clip_points_to_boundary(points_ll: gpd.GeoDataFrame, boundary_ll: gpd.GeoDataFrame):
    # make sure CRS matches
    if boundary_ll.crs != points_ll.crs:
        boundary_ll = boundary_ll.to_crs(points_ll.crs)
    # spatial join: keep points within boundary
    clipped = gpd.sjoin(points_ll, boundary_ll[["geometry"]], predicate="within", how="inner")
    clipped = clipped.drop(columns=[c for c in clipped.columns if c.startswith("index_")], errors="ignore")
    return clipped

def nearest_distances_m(points_ll: gpd.GeoDataFrame, sensors_ll: gpd.GeoDataFrame):
    pts = points_ll.to_crs(UTM43)
    sen = sensors_ll.to_crs(UTM43)
    X = np.c_[pts.geometry.x, pts.geometry.y]
    Y = np.c_[sen.geometry.x, sen.geometry.y]
    nn = NearestNeighbors(n_neighbors=1, algorithm="ball_tree")
    nn.fit(Y)
    dist_m, idx = nn.kneighbors(X, return_distance=True)
    return dist_m[:, 0], idx[:, 0]

def main():
    print("➡️ reading boundary ...")
    boundary = read_boundary()
    b_utm = boundary.to_crs(UTM43)
    bxmin, bymin, bxmax, bymax = b_utm.total_bounds
    print(f"   boundary span ~ {(bxmax-bxmin)/1000:.1f} km × {(bymax-bymin)/1000:.1f} km")

    print("➡️ reading exposure cells ...")
    exp = read_exposure()
    print(f"   cells loaded (raw): {len(exp):,}")

    # clip exposure points to the boundary
    exp = clip_points_to_boundary(exp, boundary)
    print(f"   cells after clip:   {len(exp):,}")

    exp_utm = exp.to_crs(UTM43)
    xmin, ymin, xmax, ymax = exp_utm.total_bounds
    print(f"   exposure span ~ {(xmax-xmin)/1000:.1f} km × {(ymax-ymin)/1000:.1f} km (should be close to boundary span)")

    print("➡️ reading sensors ...")
    sensors = read_sensors()
    print(f"   sensors loaded: {len(sensors)}")

    print("➡️ computing nearest-sensor distance ...")
    dist_m, _ = nearest_distances_m(exp, sensors)
    exp["dist_to_sensor_m"] = dist_m

    # numeric fields & score
    exp["pop"]         = pd.to_numeric(exp["pop"], errors="coerce").fillna(0)
    exp["pm25_interp"] = pd.to_numeric(exp["pm25_interp"], errors="coerce")

    pop_n = minmax(exp["pop"].values)
    pm_n  = minmax(np.nan_to_num(exp["pm25_interp"].values, nan=np.nanmedian(exp["pm25_interp"].values)))
    far_n = minmax(exp["dist_to_sensor_m"].values)

    w_pop, w_pm, w_far = 0.40, 0.35, 0.25
    exp["score"] = w_pop*pop_n + w_pm*pm_n + w_far*far_n

    ranked = exp.sort_values("score", ascending=False).reset_index(drop=True)

    OUT.mkdir(exist_ok=True)
    csv_fp  = OUT / "site_ranking.csv"
    gpkg_fp = OUT / "site_ranking.gpkg"

    print(f"➡️ writing {csv_fp} ...")
    ranked[["cell_id" if "cell_id" in ranked.columns else ranked.reset_index().index.name,
             "pop","pm25_interp","dist_to_sensor_m","score"]].to_csv(csv_fp, index=False)

    # remove old gpkg to avoid FID uniqueness errors
    if gpkg_fp.exists():
        gpkg_fp.unlink()

    print(f"➡️ writing {gpkg_fp} ...")
    ranked.to_file(gpkg_fp, layer="ranked_cells", driver="GPKG")

    print("\n🏁 top 10 candidate cells:")
    print(ranked[["cell_id","pop","pm25_interp","dist_to_sensor_m","score"]].head(10).to_string(index=False))
    print(f"\n   max dist_to_sensor_m: {ranked['dist_to_sensor_m'].max():.0f} m")

if __name__ == "__main__":
    main()
