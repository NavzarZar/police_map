import geopandas as gpd
import numpy as np
import pandas as pd

gdf = gpd.read_file("geo/london_lsoa.geojson")

gdf = gdf.to_crs(epsg=3395)  
gdf["area_km2"] = gdf.geometry.area / 1e6

codes = gdf["lsoa21cd"].values
areas = gdf["area_km2"].values

np.random.seed(69)

forecast_counts = np.random.poisson(lam=20, size=len(codes))

observed_counts = np.maximum(
    0,
    np.round(forecast_counts * (1 + 0.2 * np.random.randn(len(codes))))
).astype(int)

df_forecast = pd.DataFrame({
    "lsoa_code": codes,
    "forecast": forecast_counts,
    "area_km2": areas
})

df_real = pd.DataFrame({
    "lsoa_code": codes,
    "observed": observed_counts,
    "area_km2": areas
})

df_forecast.to_csv("data/mock_forecast.csv", index=False)
df_real.to_csv("data/mock_real.csv", index=False)

print(f"Generated {len(codes)} rows in each of:")
