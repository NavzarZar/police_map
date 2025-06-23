# Police Allocation Map

A Streamlit app for visualizing and optimizing police patrols in London wards using crime predictions or historical burglary data.

## Features
- Interactive Folium maps for wards and crime data.
- Supports uploaded forecast grids or historical burglary data.
- Optimizes patrol allocation using PuLP.
- Displays allocation metrics (hours, utilization, officers needed).

## Files
- `app.py`: Streamlit app for UI and map visualization.
- `police_allocation.py`: Patrol optimization logic.
- `map_viz.py`: Folium map creation functions.
- `geo/`: Contains `london_wards.geojson`, `lsoa_with_wards.geojson`, `residential_landuse.gpkg`.
- `historical/`: Historical burglary CSVs (`burglary_YYYY_MM.csv`).
- `data/`: Model predictions (`model_predictions.geojson`).

## Requirements
- Python 3.8+
- Install dependencies.
- Key libraries: `streamlit`, `geopandas`, `folium`, `pulp`, `pandas`, `numpy`.

## Setup
1. Clone repo.
2. Install dependencies.
3. Ensure `geo/`, `historical/`, and `data/` have required files.

## Usage
1. Run app:
   streamlit run app.py
2. Access at `http://localhost:8501`.
3. Select data source, ward, and view map/metrics.

## Notes
- Constraints of 100 officers, 2-hour shifts, 4 days/week.
- Can adjust `num_officers` or coverage (`c = 2.6 km²/hour`) in `police_allocation.py` if needed.
- Forecast files need `predicted_crime` column.