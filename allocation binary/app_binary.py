import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
from map_viz_binary import make_map, display_map
from allocate_officers import allocate_officers
from generate_patrol_points import generate_patrol_points

st.set_page_config(page_title="Binary Forecast Map", layout="wide")
st.title("Binary Burglary Forecast Map")

st.sidebar.header("Upload forecast CSV")
forecast_file = st.sidebar.file_uploader("Upload binary forecast CSV", type=["csv"], key="forecast")

if forecast_file:
    try:

        df = pd.read_csv(forecast_file)

        required = {"lsoa_code", "forecast", "area_km2", "ward_code"}
        if not required.issubset(df.columns):
            raise ValueError(f"Missing required columns: {required - set(df.columns)}")

        df["forecast"] = df["forecast"].astype(int).clip(0, 1)

        gdf = gpd.read_file("../geo/london_lsoa_with_wards.geojson")
        merged = gdf.merge(df, left_on="lsoa21cd", right_on="lsoa_code", how="inner")

        merged = allocate_officers(merged)

        # patrol_gdf = generate_patrol_points(merged)
        # print("Generated patrol points:", len(patrol_gdf))

        # Group by LSOA and collect points as list of (lat, lon) tuples
        
        #patrol_by_lsoa = (
        #    patrol_gdf
        #    .assign(coords=lambda df: list(zip(df.geometry.y, df.geometry.x)))
        #   .groupby("lsoa_code")["coords"]
        #    .apply(list)
        #    .rename("patrol_points")
        #)
        

        # Merge patrol points back into main LSOA GeoDataFrame
        # merged = merged.merge(patrol_by_lsoa, left_on="lsoa21cd", right_index=True, how="left")

        # print(merged["geometry"].is_valid.value_counts())
        # print(merged["geometry"].geom_type.unique())


        m = make_map(merged)
        display_map(st, m, width=700, height=500)

        # Show metrics
        st.markdown("### Summary")
        total_predicted = int(merged["forecast"].sum())
        total_officers = int(merged["officers"].sum())
        st.metric("Predicted burglary areas", int(df["forecast"].sum()))
        st.metric("Predicted safe areas", int((df["forecast"] == 0).sum()))
        st.metric("Total officers allocated", total_officers)
        st.metric("Average officers per ward", total_officers / merged["ward_code"].nunique())

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Upload a CSV with columns: lsoa_code, forecast (0 or 1), area_km2 and ward_code.")
