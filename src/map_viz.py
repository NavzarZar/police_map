import folium
from branca.colormap import linear
from streamlit_folium import folium_static
from streamlit.components.v1 import html

def make_map(gdf, value_col="prevented", code_col="lsoa21cd", legend_name="Prevented burglaries"):
    m = folium.Map(
        location=[51.5074, -0.1278],
        zoom_start=10,
        tiles=None,
        crs="EPSG3857"
    )

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
        attr="CartoDB",
        name="Light Grey",
        control=False,
    ).add_to(m)

    vmax = gdf[value_col].max()
    vmin = gdf[value_col].min()
    colormap = linear.YlOrRd_09.scale(vmin, vmax)
    colormap.caption = legend_name
    colormap.add_to(m)

    folium.GeoJson(
        gdf,
        style_function=lambda feat: {
            "fillColor": colormap(feat["properties"][value_col]),
            "color": "#444",
            "weight": 0.3,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[code_col, value_col],
            aliases=["LSOA", "Prevented"],
            localize=True,
            labels=True,
        ),
        name="LSOA choropleth",
    ).add_to(m)

    return m

def display_map(streamlit_app, m, width=700, height=500):
    map_html = m._repr_html_()
    html(map_html, width=width, height=height)