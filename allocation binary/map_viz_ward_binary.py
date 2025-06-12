import folium
import json
from streamlit.components.v1 import html
import streamlit as st

def make_ward_map(ward_gdf, lsoa_gdf, selected_display_month=None):
    # Center map on London
    m = folium.Map(
        location=[51.5074, -0.1278],
        zoom_start=10,
        tiles="cartodbpositron",
        control_scale=True
    )

    max_forecast = ward_gdf["forecast"].max()
    min_forecast = ward_gdf["forecast"].min()
    forecast_range = max_forecast - min_forecast if max_forecast != min_forecast else 1

    def get_color(forecast):
        norm_forecast = (forecast - min_forecast) / forecast_range
        r = int(255)
        g = int(50 + 100 * (1 - norm_forecast))
        b = int(50 + 100 * (1 - norm_forecast))
        return f"rgb({r},{g},{b})"

    # JavaScript for click event to set session state
    click_js = """
    function(feature, layer) {
        layer.on('click', function(e) {
            // Store ward_code in session state via Streamlit
            var ward_code = feature.properties.ward_code;
            // Use Streamlit's set_session_state
            window.parent.postMessage({
                type: 'streamlit:set_session_state',
                key: 'selected_ward',
                value: ward_code
            }, '*');
        });
    }
    """

    # Adjust tooltip based on whether historical month is selected
    tooltip_fields = ["ward_code", "forecast", "officers", "lsoa_count"]
    tooltip_aliases = ["Ward Code", "Burglaries" if selected_display_month else "Predicted Burglaries", "Officers Allocated", "LSOA Count"]

    folium.GeoJson(
        ward_gdf,
        style_function=lambda feat: {
            "fillColor": get_color(feat["properties"]["forecast"]),
            "color": "#333",
            "weight": 1,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
        ),
        highlight_function=lambda x: {"weight": 3, "color": "#000", "fillOpacity": 0.9},
        popup=folium.GeoJsonPopup(
            fields=["ward_code"],
            aliases=["Ward Code"],
            labels=True
        ),
        embed=True,
        function=click_js
    ).add_to(m)

    legend_html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; padding: 10px; background-color: white; border: 2px solid grey; border-radius: 5px;">
        <h4>Map Legend (Wards)</h4>
        <p><i style="background: rgb(255,50,50); width: 20px; height: 20px; display: inline-block;"></i> {'High amount of burglaries' if selected_display_month else 'High predicted burglaries'}</p>
        <p><i style="background: rgb(255,150,150); width: 20px; height: 20px; display: inline-block;"></i> {'Low amount of burglaries' if selected_display_month else 'Low predicted burglaries'}</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

def make_lsoa_map(gdf):
    # Center map on the selected ward
    centroid = gdf.geometry.centroid.iloc[0]
    m = folium.Map(
        location=[centroid.y, centroid.x],
        zoom_start=13,
        tiles="cartodbpositron",
        control_scale=True
    )

    max_area = gdf["area_km2"].max()
    min_area = gdf["area_km2"].min()
    area_range = max_area - min_area if max_area != min_area else 1

    def get_color(forecast, area_km2):
        norm_area = (area_km2 - min_area) / area_range
        if forecast == 1:
            r = int(255)
            g = int(50 + 100 * (1 - norm_area))
            b = int(50 + 100 * (1 - norm_area))
        else:
            r = int(50 + 100 * norm_area)
            g = int(150 + 100 * norm_area)
            b = int(255)
        return f"rgb({r},{g},{b})"

    folium.GeoJson(
        gdf,
        style_function=lambda feat: {
            "fillColor": get_color(feat["properties"]["forecast"], feat["properties"]["area_km2"]),
            "color": "#333",
            "weight": 0.5,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["lsoa21cd", "forecast", "ward_code", "officers"],
            aliases=["LSOA", "Forecasted", "Ward", "Officers Allocated"],
            localize=True,
            labels=True,
        ),
        highlight_function=lambda x: {"weight": 2, "color": "#000", "fillOpacity": 0.9},
    ).add_to(m)

    # Add patrol points
    for idx, row in gdf.iterrows():
        for lat, lon in row["patrol_points"]:
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,
                color="black",
                fill=True,
                fill_color="black",
                fill_opacity=0.6,
            ).add_to(m)

    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; padding: 10px; background-color: white; border: 2px solid grey; border-radius: 5px;">
        <h4>Map Legend (LSOAs)</h4>
        <p><i style="background: rgb(255,50,50); width: 20px; height: 20px; display: inline-block;"></i> High-risk LSOA (large area)</p>
        <p><i style="background: rgb(255,150,150); width: 20px; height: 20px; display: inline-block;"></i> High-risk LSOA (small area)</p>
        <p><i style="background: rgb(50,150,255); width: 20px; height: 20px; display: inline-block;"></i> Safe LSOA (small area)</p>
        <p><i style="background: rgb(150,250,255); width: 20px; height: 20px; display: inline-block;"></i> Safe LSOA (large area)</p>
        <p><i style="background: black; width: 10px; height: 10px; border-radius: 50%; display: inline-block;"></i> Patrol Point</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m

def display_map(streamlit_app, m, width=900, height=600):
    map_html = m._repr_html_()
    html(map_html, width=width, height=height)