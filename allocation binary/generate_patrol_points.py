import numpy as np
import geopandas as gpd
from shapely.geometry import Point

def generate_patrol_points(gdf, officer_col="officers", max_points_per_lsoa=50):

    patrol_points = []

    for _, row in gdf.iterrows():
        num_officers = int(row[officer_col])
        if num_officers == 0 or row.geometry.is_empty:
            continue

        polygon = row.geometry

        count = min(num_officers, max_points_per_lsoa)
        for _ in range(count):
            tries = 0
            while tries < 10:
                minx, miny, maxx, maxy = polygon.bounds
                p = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
                if polygon.contains(p):
                    p_wgs84 = gpd.GeoSeries([p], crs=gdf.crs).to_crs(epsg=4326).iloc[0]
                    patrol_points.append({"lsoa_code": row["lsoa21cd"], "geometry": p_wgs84})
                    break
                tries += 1

    return gpd.GeoDataFrame(patrol_points, geometry="geometry", crs=gdf.crs)
