import folium
from streamlit_folium import folium_static
from streamlit.components.v1 import html
import geopandas as gpd

# Create the full ward map
def make_map_full(wards_gdf, ward_code_col):
    wards_wgs = wards_gdf.to_crs(epsg=4326)
    m = folium.Map(tiles=None)
    minx, miny, maxx, maxy = wards_wgs.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])
    folium.GeoJson(
        wards_wgs,
        style_function=lambda f: {"fillOpacity": 0, "color": "#444", "weight": 0.5},
        tooltip=folium.GeoJsonTooltip(fields=[ward_code_col]),
        name="All wards",
    ).add_to(m)
    return m

# Create a map for a specific ward with grid cells
def make_ward_grid_map(wards_gdf, grid_gdf, selected_ward_code, ward_code_col, crime_col):
    ward_gdf = wards_gdf[wards_gdf[ward_code_col] == selected_ward_code]
    wards_wgs = wards_gdf.to_crs(epsg=4326)
    ward_wgs = ward_gdf.to_crs(epsg=4326)
    grid_gdf = grid_gdf.to_crs(epsg=4326)
    ward_geom = ward_wgs.geometry.squeeze()
    m = folium.Map(tiles=None)
    minx, miny, maxx, maxy = ward_wgs.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])
    folium.GeoJson(
        wards_wgs,
        style_function=lambda f: {"fillOpacity": 0, "color": "#999", "weight": 0.5},
        name="All wards"
    ).add_to(m)
    folium.GeoJson(
        ward_wgs,
        style_function=lambda f: {"color": "#000", "weight": 2, "fillOpacity": 0},
        name="Selected ward"
    ).add_to(m)
    cells = grid_gdf[grid_gdf.intersects(ward_geom)]
    for _, cell in cells.iterrows():
        minx, miny, maxx, maxy = cell.geometry.bounds
        rect_bounds = [[miny, minx], [maxy, maxx]]
        folium.Rectangle(
            bounds=rect_bounds,
            fill=True,
            stroke=False,
            fill_color="#f03",
            fill_opacity=0.6 if cell[crime_col] == 1 else 0,
        ).add_to(m)
    return m

# Create a map for a specific ward with LSOAs and burglary data
def make_ward_lsoa_map(wards_gdf, lsoa_gdf, burglary_data, selected_ward_code, ward_code_col, lsoa_code_col, crime_col):
    ward_gdf = wards_gdf[wards_gdf[ward_code_col] == selected_ward_code]
    wards_wgs = wards_gdf.to_crs(epsg=4326)
    ward_wgs = ward_gdf.to_crs(epsg=4326)
    lsoa_gdf = lsoa_gdf.to_crs(epsg=4326)
    ward_geom = ward_wgs.geometry.squeeze()
    m = folium.Map(tiles=None)
    minx, miny, maxx, maxy = ward_wgs.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])
    folium.GeoJson(
        wards_wgs,
        style_function=lambda f: {"fillOpacity": 0, "color": "#999", "weight": 0.5},
        name="All wards"
    ).add_to(m)
    folium.GeoJson(
        ward_wgs,
        style_function=lambda f: {"color": "#000", "weight": 2, "fillOpacity": 0},
        name="Selected ward"
    ).add_to(m)
    # Filter LSOAs within the selected ward
    lsoas_in_ward = lsoa_gdf[lsoa_gdf[ward_code_col] == selected_ward_code]
    # Merge LSOA data with burglary data
    lsoas_with_burglary = lsoas_in_ward.merge(burglary_data, left_on=lsoa_code_col, right_on="lsoa_code", how="left")
    # Add LSOAs to the map
    folium.GeoJson(
        lsoas_with_burglary,
        style_function=lambda f: {
            "fillColor": "#f03" if f["properties"].get(crime_col, 0) == 1 else "#0000",
            "fillOpacity": 0.6 if f["properties"].get(crime_col, 0) == 1 else 0,
            "color": "#444",
            "weight": 0.5
        },
        tooltip=folium.GeoJsonTooltip(fields=[lsoa_code_col, crime_col], aliases=["LSOA Code", "Burglary"]),
        name="LSOAs"
    ).add_to(m)
    return m

# Display the map in a Streamlit app
def display_map(streamlit_app, m, width=700, height=500):
    map_html = m._repr_html_()
    html(map_html, width=width, height=height)