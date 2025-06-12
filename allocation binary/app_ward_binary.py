import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import os
from datetime import datetime
from map_viz_ward_binary import make_ward_map, make_lsoa_map, display_map

st.set_page_config(page_title="Binary Map", layout="wide")
st.title("Binary Burglary Map")

st.components.v1.html(
    '<script src="streamlit_map.js"></script>',
    height=0,
)

# Initialize session state
if "selected_ward" not in st.session_state:
    st.session_state.selected_ward = None
if "selected_month" not in st.session_state:
    st.session_state.selected_month = None
if "selected_display_month" not in st.session_state:
    st.session_state.selected_display_month = None
if "last_action" not in st.session_state:
    st.session_state.last_action = None

# Callback for file upload
def handle_file_upload():
    if st.session_state.forecast:
        st.session_state.last_action = "upload"
        st.session_state.selected_ward = None
        st.session_state.selected_month = None
        st.session_state.selected_display_month = None

# Sidebar for data selection
st.sidebar.header("Upload forecast CSV")
forecast_file = st.sidebar.file_uploader(
    "Upload binary forecast CSV",
    type=["csv"],
    key="forecast",
    on_change=handle_file_upload
)

# Prioritize uploaded file
if forecast_file and st.session_state.last_action != "upload":
    st.session_state.last_action = "upload"
    st.session_state.selected_ward = None
    st.session_state.selected_month = None
    st.session_state.selected_display_month = None
    st.rerun()

# Dropdown for historical data
st.sidebar.header("View Historical Data")
historical_files = [f for f in os.listdir("../historical") if f.startswith("burglary_") and f.endswith(".csv")]
# Extract and sort YYYY_MM chronologically
month_strings = []
for f in historical_files:
    month_str = f.replace("burglary_", "").replace(".csv", "")
    try:
        datetime.strptime(month_str.replace("_", "-"), "%Y-%m")
        month_strings.append(month_str)
    except ValueError:
        continue
month_strings.sort()

# Map sorted YYYY_MM to display names
month_map = {}
for month_str in month_strings:
    dt = datetime.strptime(month_str.replace("_", "-"), "%Y-%m")
    display_name = dt.strftime("%B %Y")
    month_map[display_name] = month_str

month_options = ["None"] + list(month_map.keys())
selected_display_month = st.sidebar.selectbox("Select historical month", month_options, key="month_selector")

# Map selected display name back to YYYY_MM
selected_month = month_map.get(selected_display_month, None) if selected_display_month != "None" else None

# Update last_action if a month is selected
if selected_month != st.session_state.selected_month or selected_display_month != st.session_state.selected_display_month:
    if not forecast_file:
        st.session_state.selected_month = selected_month
        st.session_state.selected_display_month = selected_display_month
        if selected_month:
            st.session_state.last_action = "month"
            st.session_state.selected_ward = None
            st.rerun()

# Determine data source based on last action
data_source = None
if forecast_file:
    data_source = forecast_file
elif st.session_state.selected_month:
    data_source = f"../historical/burglary_{st.session_state.selected_month}.csv"


# Debug state
#st.sidebar.write(f"Debug: last_action={st.session_state.last_action}, forecast_file={bool(forecast_file)}, selected_month={st.session_state.selected_month}")

if data_source:
    try:
        # Read and validate CSV
        if isinstance(data_source, str):
            df = pd.read_csv(data_source)
        else:
            df = pd.read_csv(data_source)
        required = {"lsoa_code", "forecast", "area_km2", "ward_code"}
        if not required.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required - set(df.columns)}")

        # Validate data
        if df["area_km2"].lt(0).any():
            raise ValueError("area_km2 contains negative values")
        if not df["forecast"].isin([0, 1]).all():
            raise ValueError("forecast column must contain only 0 or 1")

        df["forecast"] = df["forecast"].astype(int)

        # Load LSOA GeoJSON and merge
        lsoa_gdf = gpd.read_file("../geo/london_lsoa_with_wards.geojson")
        merged_lsoa = lsoa_gdf.merge(df, left_on="lsoa21cd", right_on="lsoa_code", how="inner")

        if merged_lsoa.empty:
            raise ValueError("No matching LSOA codes found between CSV and GeoJSON")

        # Allocate officers
        from allocate_officers import allocate_officers
        merged_lsoa = allocate_officers(merged_lsoa)

        # Generate patrol points
        from generate_patrol_points import generate_patrol_points
        patrol_gdf = generate_patrol_points(merged_lsoa)
        patrol_by_lsoa = (
            patrol_gdf
            .assign(coords=lambda df: list(zip(df.geometry.y, df.geometry.x)))
            .groupby("lsoa_code")["coords"]
            .apply(list)
            .rename("patrol_points")
        )
        merged_lsoa = merged_lsoa.merge(patrol_by_lsoa, left_on="lsoa21cd", right_index=True, how="left")
        merged_lsoa["patrol_points"] = merged_lsoa["patrol_points"].fillna("").apply(list)

        # Create ward-level GeoDataFrame
        ward_gdf = gpd.GeoDataFrame(
            merged_lsoa.dissolve(by="ward_code", aggfunc={
                "forecast": "sum",
                "area_km2": "sum",
                "officers": "sum",
                "lsoa21cd": "count"
            }).reset_index()
        )
        ward_gdf = ward_gdf.rename(columns={"lsoa21cd": "lsoa_count"})

        # Display ward-level map if no ward is selected
        if st.session_state.selected_ward is None:
            st.markdown(f"### London Wards{' - ' + st.session_state.selected_display_month if st.session_state.selected_display_month else ''}")
            m = make_ward_map(ward_gdf, merged_lsoa, st.session_state.selected_display_month)
            display_map(st, m, width=900, height=600)

            # Show ward-level metrics
            st.markdown(f"### Summary (All Wards{' - ' + st.session_state.selected_display_month if st.session_state.selected_display_month else ''})")
            total_predicted = int(merged_lsoa["forecast"].sum())
            total_officers = int(merged_lsoa["officers"].sum())
            st.metric("Burglary areas (LSOAs)", total_predicted)
            st.metric("Safe LSOAs", len(merged_lsoa) - total_predicted)
            st.metric("Total officers allocated", total_officers)
            st.metric("Average officers per ward", round(total_officers / ward_gdf["ward_code"].nunique(), 1))

        # Display LSOA-level map for selected ward
        else:
            selected_ward = st.session_state.selected_ward
            st.markdown(f"### LSOAs in Ward {selected_ward}{' - ' + st.session_state.selected_display_month if st.session_state.selected_display_month else ''}")
            ward_lsoa_gdf = merged_lsoa[merged_lsoa["ward_code"] == selected_ward]
            if ward_lsoa_gdf.empty:
                st.error(f"No LSOAs found for ward {selected_ward}")
            else:
                m = make_lsoa_map(ward_lsoa_gdf)
                display_map(st, m, width=900, height=600)

                # Show LSOA-level metrics for the ward
                st.markdown(f"### Summary for Ward {selected_ward}{' - ' + st.session_state.selected_display_month if st.session_state.selected_display_month else ''}")
                total_predicted = int(ward_lsoa_gdf["forecast"].sum())
                total_officers = int(ward_lsoa_gdf["officers"].sum())
                st.metric("Predicted burglary areas (LSOAs)", total_predicted)
                st.metric("Safe LSOAs", len(ward_lsoa_gdf) - total_predicted)
                st.metric("Total officers allocated", total_officers)
                st.metric("Number of LSOAs in ward", len(ward_lsoa_gdf))

            # Button to return to ward-level map
            if st.button("Back to Ward Map"):
                st.session_state.selected_ward = None
                st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Upload a forecast CSV with columns: lsoa_code, forecast (0 or 1), area_km2, and ward_code, or select a historical month.")

# Display active data source
if data_source:
    source_name = "Uploaded Forecast" if st.session_state.last_action == "upload" else f"Historical Data ({st.session_state.selected_display_month})"
    st.sidebar.info(f"Displaying: {source_name}")


# Debug state
#st.sidebar.write(f"Debug: last_action={st.session_state.last_action}, forecast_file={bool(forecast_file)}, selected_month={st.session_state.selected_month}, data_source_type={type(data_source).__name__}")