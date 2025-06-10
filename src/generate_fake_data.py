import geopandas as gpd
from shapely.geometry import box
import numpy as np

wards = gpd.read_file("geo/london_wards.geojson")

wards_m = wards.to_crs(epsg=3857)
xmin, ymin, xmax, ymax = wards_m.total_bounds

# build a 500×500 m grid covering all wards
cell_size = 250  
xs = np.arange(xmin, xmax, cell_size)
ys = np.arange(ymin, ymax, cell_size)

polygons = []
for x in xs:
    for y in ys:
        polygons.append(box(x, y, x + cell_size, y + cell_size))

grid = gpd.GeoDataFrame(geometry=polygons, crs=wards_m.crs)

grid["predicted_crime"] = np.random.choice([0, 1], size=len(grid))

grid = grid.to_crs(epsg=4326)
grid.to_file("data/grid.geojson", driver="GeoJSON")
