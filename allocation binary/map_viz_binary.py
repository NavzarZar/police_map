import folium
from streamlit.components.v1 import html

def make_map(gdf, value_col="forecast", code_col="lsoa21cd", ward_col="ward_code", patrol_points=None):
    m = folium.Map(
        location=[51.5074, -0.1278],
        zoom_start=10,
        tiles="cartodbpositron"
    )

    max_area = gdf["area_km2"].max()
    min_area = gdf["area_km2"].min()
    area_range = max_area - min_area

    def get_color(forecast, area_km2):
        norm_area = (area_km2 - min_area) / area_range if area_range != 0 else 0.5

        if forecast == 1:
            intensity = norm_area
            r = int(255)
            g = int(75 * (1 - intensity))
            b = int(75 * (1 - intensity))
        else:
            intensity = 1 - norm_area
            r = int(200 * intensity) + 20
            g = int(200 + 55 * intensity)
            b = int(200 * intensity) + 20

        return f"rgb({r},{g},{b})"

    folium.GeoJson(
        gdf,
        style_function=lambda feat: {
            "fillColor": get_color(feat["properties"][value_col], feat["properties"]["area_km2"]),
            "color": "#444",
            "weight": 0.3,
            "fillOpacity": 0.8,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[code_col, value_col, ward_col, "officers"],
            aliases=["LSOA", "Forecasted", "Ward", "Officers Allocated"],
            localize=True,
            labels=True,
        ),
    ).add_to(m)

    if "patrol_points" in gdf.columns:
        for patrols in gdf["patrol_points"].dropna():
            for lat, lon in patrols:
                ## print(f"Adding point at lat={lat}, lon={lon}")
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=0.5,
                    color="black",
                    fill=True,
                    fill_color="black",
                    fill_opacity=0.5,
                ).add_to(m)


    return m

def display_map(streamlit_app, m, width=700, height=500):
    map_html = m._repr_html_()
    html(map_html, width=width, height=height)