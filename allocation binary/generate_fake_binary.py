import geopandas as gpd
import numpy as np
import pandas as pd

gdf = gpd.read_file("../geo/london_lsoa_with_wards.geojson")

gdf = gdf.to_crs(epsg=3395)
gdf["area_km2"] = gdf.geometry.area / 1e6

codes = gdf["lsoa21cd"].values
areas = gdf["area_km2"].values
wards = gdf["Ward code"].values

np.random.seed(42)
binary_forecast = np.random.choice([0, 1], size=len(codes), p=[0.3, 0.7])

df_forecast = pd.DataFrame({
    "lsoa_code": codes,
    "forecast": binary_forecast,
    "area_km2": areas,
    "ward_code": wards
})

df_forecast.to_csv("../data/binary_mock_forecast_2.csv", index=False)

print(f"Generated binary forecast for {len(codes)} LSOAs.")
print(f"Total predicted burglary areas: {binary_forecast.sum()}")
