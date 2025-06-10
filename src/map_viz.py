import folium
from branca.colormap import linear
from streamlit_folium import folium_static
from streamlit.components.v1 import html
import geopandas as gpd

def make_map_full(wards_gdf, ward_code_col):
    # make sure we have lat lon coordinates
    wards_wgs = wards_gdf.to_crs(epsg=4326)


    # start empty and add the light map
    m = folium.Map(tiles=None)

    # fit the total bounds of the wards
    minx, miny, maxx, maxy = wards_wgs.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])

    # draw the wards
    folium.GeoJson(
        wards_wgs,
        style_function=lambda f: {"fillOpacity": 0, "color": "#444", "weight": 0.5},
        tooltip=folium.GeoJsonTooltip(fields=[ward_code_col]),
        name="All wards",
    ).add_to(m)

    return m

def make_ward_grid_map(wards_gdf, grid_gdf, selected_ward_code, ward_code_col, crime_col):
    ward_gdf = wards_gdf[wards_gdf[ward_code_col] == selected_ward_code]


    wards_wgs = wards_gdf.to_crs(epsg=4326)
    ward_wgs = ward_gdf.to_crs(epsg=4326)
    grid_gdf = grid_gdf.to_crs(epsg=4326)

    ward_geom = ward_wgs.geometry.squeeze()

    m = folium.Map(tiles=None)
    # zoom to the selected ward
    minx, miny, maxx, maxy = ward_wgs.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]])

    folium.GeoJson(
        wards_wgs,
        style_function=lambda f: {"fillOpacity": 0, "color": "#999", "weight": 0.5},
        name="All wards"
    ).add_to(m)

    # highlight the selected ward
    folium.GeoJson(
        ward_wgs,
        style_function=lambda f: {"color": "#000", "weight": 2, "fillOpacity": 0},
        name="Selected ward"
    ).add_to(m)

    # overlay the grid cells
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

   

def display_map(streamlit_app, m, width=700, height=500):
    map_html = m._repr_html_()
    html(map_html, width=width, height=height)