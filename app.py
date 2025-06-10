import streamlit as st
import geopandas as gpd
from src.data_processing import process_data
from src.map_viz import make_map_full, make_ward_grid_map, display_map


st.set_page_config(page_title="Police Allocation Map", layout="wide")
st.title("Police Allocation Map")

st.sidebar.header("Upload your data")
forecast_file = st.sidebar.file_uploader(
    "Upload grid forecast CSV", type=["geojson", "json"], key="grid"
)

if forecast_file:
    try:   
        wards = gpd.read_file("geo/london_wards.geojson")
        grid = gpd.read_file(forecast_file)

        ward_code_col = "Ward code"
        options = ["All wards"] + wards[ward_code_col].tolist()
        selection =   st.sidebar.selectbox("Map view", options)

        if selection == "All wards":
            m = make_map_full(wards, "Ward code")
        else:
            m = make_ward_grid_map(wards, grid, selected_ward_code=selection,ward_code_col=ward_code_col, crime_col="predicted_crime"
            )

        display_map(st, m, width=900, height=600)

    except Exception as e:
        st.error(f"Error while processing data: {e}")
else:
    st.info("Upload forecast grid CSV in the sidebar, please")
