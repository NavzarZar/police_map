import streamlit as st
import geopandas as gpd
import os
from datetime import datetime
from src.data_processing import process_data
from src.map_viz import make_map_full, make_ward_lsoa_map, display_map, make_ward_grid_map

st.set_page_config(page_title="Police Allocation Map", layout="wide")
st.title("Police Allocation Map")

st.sidebar.header("Select Data Source")
data_source = st.sidebar.radio("Choose data source", ["Upload Forecast", "Past Month Data"])

wards = gpd.read_file("geo/london_wards.geojson")
ward_code_col = "Ward code"
options = ["All wards"] + wards[ward_code_col].tolist()
selection = st.sidebar.selectbox("Map view", options)

if data_source == "Upload Forecast":
    st.sidebar.header("Upload your data")
    forecast_file = st.sidebar.file_uploader(
        "Upload grid forecast CSV", type=["geojson", "json"], key="grid"
    )
    if forecast_file:
        try:
            grid = gpd.read_file(forecast_file)
            if selection == "All wards":
                m = make_map_full(wards, ward_code_col)
            else:
                m = make_ward_grid_map(wards, grid, selected_ward_code=selection, ward_code_col=ward_code_col, crime_col="predicted_crime")
            display_map(st, m, width=900, height=600)
        except Exception as e:
            st.error(f"Error while processing data: {e}")
    else:
        st.info("Upload a forecast grid file in the sidebar, please")
else:
    # Past Month Data
    st.sidebar.header("Select Month")
    # Assume CSV files are named like burglaries_YYYY_MM.csv in data folder
    data_folder = "historical"
    available_months = []
    if os.path.exists(data_folder):
        available_months = [
            f for f in os.listdir(data_folder) if f.startswith("burglary_") and f.endswith(".csv")
        ]
        available_months.sort(reverse=True)  # Newest first
        # Extract YYYY_MM from filenames
        month_options = [
            datetime.strptime(f.replace("burglary_", "").replace(".csv", ""), "%Y_%m").strftime("%B %Y")
            for f in available_months
        ]
    else:
        month_options = []

    if not month_options:
        st.error("No past month data available in the data folder.")
    else:
        month_selection = st.sidebar.selectbox("Select a month", month_options)
        try:
            # Convert selected month back to filename
            selected_month = datetime.strptime(month_selection, "%B %Y").strftime("%Y_%m")
            data_file = os.path.join(data_folder, f"burglary_{selected_month}.csv")
            lsoa_data = gpd.read_file("geo/london_lsoa_with_wards.geojson")
            burglary_data = gpd.read_file(data_file)
            if selection == "All wards":
                m = make_map_full(wards, ward_code_col)
            else:
                m = make_ward_lsoa_map(
                    wards_gdf=wards,
                    lsoa_gdf=lsoa_data,
                    burglary_data=burglary_data,
                    selected_ward_code=selection,
                    ward_code_col=ward_code_col,
                    lsoa_code_col="lsoa21cd",
                    crime_col="forecast"
                )
            display_map(st, m, width=900, height=600)
        except Exception as e:
            st.error(f"Error while processing data: {e}")