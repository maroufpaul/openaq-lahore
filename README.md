# OpenAQ Lahore Sensor Placement Optimization

## Project Overview
This project develops a **data-driven model** for optimizing air-quality sensor placement in **Lahore, Pakistan**, using open data from OpenAQ, WorldPop, and OpenStreetMap. The model integrates population density and PM₂.₅ pollution data to identify **optimal sensor deployment locations** that maximize coverage and exposure monitoring efficiency.

The workflow is divided into two phases:
1. **Optimization model** – ranks potential sites for new sensors using population-weighted PM₂.₅ exposure and proximity to existing sensors.
2. **Simulation model (upcoming)** – tests sensor network performance under dynamic conditions (e.g., pollution spikes, sensor failures).

---

## Repository Structure

```
OPENAQ-LAHORE/
│
├── data/                       # Input data and boundaries
│   ├── boundary/               # Administrative and study area boundaries
│   ├── osm/                    # OSM-based geographic data (future use)
│   ├── sensors/                # Sensor datasets from OpenAQ
│   │   ├── raw/                # Individual CSVs for each sensor
│   │   ├── lahore_locations_subset.xlsx
│   │   └── lahore_pm25_sensors_subset.xlsx
│   └── worldpop/               # Population raster and derived layers
│
├── notebooks/                  # For exploratory analysis (optional)
│
├── outputs/                    # Generated results and intermediate files
│   ├── qc/                     # Quality-checked layers
│   ├── site_ranking.csv        # Final ranked sites (for export and mapping)
│   ├── site_ranking.gpkg       # Ranked candidate grid (for QGIS visualization)
│   └── top10_sites.gpkg        # Top 10 optimal locations
│
├── src/                        # Core scripts
│   ├── aggregate_sensor_timeseries.py
│   ├── prepare_sensors.py
│   ├── rank_sites.py
│   ├── utils_geo.py
│   ├── utils_idw.py
│   └── __init__.py
│
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/openaq-lahore.git
cd openaq-lahore
```

### 2. Set up virtual environment
```bash
python -m venv .venv
.\.venv\Scripts ctivate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch QGIS (optional)
To visualize intermediate or final outputs, open QGIS and load:
- `data/boundary/lahore_boundary.geojson`
- `outputs/site_ranking.gpkg`
- `outputs/top10_sites.gpkg`

---

## Workflow Summary

### Step 1 – Data Preparation
- Extract OpenAQ PM₂.₅ data using provided sensor CSVs.
- Clip WorldPop population raster to Lahore boundary.
- Convert to centroid grid for integration with pollution surface.

### Step 2 – Pollution Surface Generation
- Interpolate PM₂.₅ levels using **Inverse Distance Weighting (IDW)** in QGIS or Python.
- Export interpolated raster as `pm25_idw_lahore.tif`.

### Step 3 – Population–Pollution Exposure
- Combine population and PM₂.₅ rasters to create a **population-weighted exposure grid**.
- Output: `population_pm25_exposure.gpkg`.

### Step 4 – Sensor Ranking
Run the ranking script:
```bash
python -m src.rank_sites
```
This script:
- Computes distance to nearest existing sensor.
- Scores each grid cell using combined exposure and coverage metrics.
- Produces ranked candidate sites for new sensors.

### Step 5 – Visualization in QGIS
- Load `site_ranking.gpkg` → symbolize by `score` (yellow = low, red = high).
- Load `top10_sites.gpkg` → style with bright red circles and white borders.
- Export the final map (Figure 5 in report).

---

## Key Outputs

| File | Description |
|------|--------------|
| **pm25_idw_lahore.tif** | Interpolated PM₂.₅ surface (µg/m³) |
| **population_pm25_exposure.gpkg** | Combined population-weighted exposure map |
| **site_ranking.csv / .gpkg** | Ranked candidate sites for new sensors |
| **top10_sites.gpkg** | Top 10 optimal sensor locations for visualization |

---

## Next Steps (Phase 2)
The next phase will introduce a **simulation component** to test the optimized network under uncertainty. Using Monte Carlo or agent-based modeling, the simulation will evaluate:
- Robustness of coverage under sensor failures.
- Detection efficiency during pollution spikes.
- Trade-offs between cost, coverage, and redundancy.

---

## Acknowledgments
Developed as part of a collaboration with **OpenAQ** to promote equitable air-quality monitoring access.  
Student contributors: *Marouf Paul* & *Joyce Zhang* (Fall 2025).
