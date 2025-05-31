import streamlit as st
import geopandas as gpd
from src.data_processing import process_data
from src.map_viz import make_map, display_map

st.set_page_config(page_title="Police Allocation Map", layout="wide")
st.title("Police Allocation + Prevention Map")

st.sidebar.header("Upload your mock data")
forecast_file = st.sidebar.file_uploader(
    "Upload forecast CSV", type=["csv"], key="forecast"
)
real_file = st.sidebar.file_uploader(
    "Upload real CSV", type=["csv"], key="real"
)

st.sidebar.header("The parameters")
officer_hours = st.sidebar.number_input(
    "Officer-hours per ward(weekly)", value=800, step=50
)

elasticity = st.sidebar.slider(
    "Burglary elasticity", min_value=-1.0, max_value=0.0, value=-0.3, step=0.05
)

if forecast_file and real_file:
    try:
        df = process_data(
            forecast_file,
            real_file,
            officer_hours=officer_hours,
            elasticity=elasticity
        )

        gdf = gpd.read_file("geo/london_lsoa.geojson")
        merged = gdf.merge(
            df,
            left_on="lsoa21cd",
            right_on="lsoa_code",
            how="inner"
        )

        m = make_map(
            merged,
            value_col="prevented",
            code_col="lsoa21cd",
            legend_name="Prevented burglaries"
        )


        display_map(st, m, width=900, height=600)


        col1, col2, col3 = st.columns(3)
        total_obs = int(merged["observed"].sum())
        total_prevented = int(merged["prevented"].sum())

        col1.metric("Total observed burglaries", f"{total_obs}")
        col2.metric("Total prevented", f"{total_prevented}")
        col3.metric("Elasticity", f"{elasticity}")


    except Exception as e:
        st.error(f"Error while processing data: {e}")
else:
    st.info("Upload forecast and real data CSVs in the sidebar, please")


st.markdown(
    """
    **CSV format**
    - You need both to have a column 'lsoa_code',
    - forecast csv needs 'forecast' and 'area_km2',
    - real data csv needs 'observed' and 'area_km2'

    """
)