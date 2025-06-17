import geopandas as gpd
import pulp
import pandas as pd
import numpy as np

grid = gpd.read_file('data/model_predictions.geojson')  
grid = grid[grid['predicted_crime'] == 1].copy()
grid = grid.to_crs("EPSG:27700")  
grid['cell_id'] = grid.index.astype(int)

res = gpd.read_file('geo/residential_landuse.gpkg').to_crs("EPSG:27700")

inter = gpd.overlay(grid[['cell_id', 'geometry']],
                    res[['geometry']],
                    how='intersection'
)

inter['res_area'] = inter.geometry.area
res_sum = (
    inter
    .groupby('cell_id')['res_area']
    .sum()
    .reset_index()
)

grid = grid.merge(res_sum, on='cell_id', how='left')
grid['res_area'] = grid['res_area'].fillna(0)
grid['res_frac'] = grid['res_area'] / grid.geometry.area
grid['S_g'] = (grid.geometry.area / 1e6) * grid['res_frac']  # Convert area to km²

wards = gpd.read_file('geo/london_wards.geojson')
grid['centroid'] = grid.geometry.centroid

left  = grid.set_geometry('centroid')
right = wards[['Ward code','geometry']]

centroids = gpd.sjoin(
    left,
    right,
    how='left',
    predicate='within'
)

grid = grid.join(centroids['Ward code'])
grid = grid.drop(columns=['centroid']).set_geometry('geometry')

# Parameters
c = 2.6 # coverage in km2 per hour
grid['t_g'] = np.ceil(grid['S_g'] / c).astype(int)
days   = list(range(1, 8))                 
blocks = ['06-18', '18-22']
W_d = {d: 1/7 for d in days}
V_b = {'06-18': 0.6, '18-22': 0.4}
num_officers = 100
I = range(1, num_officers + 1)

def solve_ward(ward_code):

    ward_cells = grid[grid['Ward code'] == ward_code]
    ward_cells = ward_cells[ward_cells['S_g'] > 0] 
    G = ward_cells['cell_id'].tolist()
    t_g = ward_cells.set_index('cell_id')['t_g'].to_dict()


    prob = pulp.LpProblem(f"Ward_{ward_code}_Patrol", pulp.LpMaximize)
    y = pulp.LpVariable.dicts('y', (I, days), cat='Binary')
    x = pulp.LpVariable.dicts('x', (I, G, days, blocks), lowBound=0, cat='Integer')

    prob += pulp.lpSum(
        W_d[d]*V_b[b]* x[i][g][d][b] / t_g[g]
        for i in I for g in G for d in days for b in blocks
    )

    # 2 hrs + 4 day /week 
    for i in I:
        prob += pulp.lpSum(y[i][d] for d in days) <= 4
        for d in days:
            prob += pulp.lpSum(x[i][g][d][b] for g in G for b in blocks) <= 2 * y[i][d]

    
    for g in G:
        tg = t_g[g]
        for d in days:
            for b in blocks:
                prob += pulp.lpSum(x[i][g][d][b] for i in I) <= tg

    
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    print(f"  → {len(prob.variables())} vars, {len(prob.constraints)} constraints")


    rows = []
    for i in I:
        for g in G:
            for d in days:
                for b in blocks:
                    h = int(pulp.value(x[i][g][d][b]))
                    if h>0:
                        rows.append({
                            'ward_id':  ward_code,
                            'officer':  i,
                            'cell':     g,
                            'day':      d,
                            'block':    b,
                            'hours':    h
                        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    ward_code = 'E05013570'
    df = solve_ward(ward_code)
    if df.empty:
        print(f"No patrol assignments for ward {ward_code}. Perhaps no cells are in this ward.")
    else:
        actual = df['hours'].sum()
        # total hours needed for perfect coverage
        ward_cells = grid[grid['Ward code']=='E05013570']
        total_needed = (ward_cells['t_g']
                        .repeat(len(days)*len(blocks))
                        .sum())
        coverage_frac = actual / total_needed
        print(f"Coverage achieved: {coverage_frac:.0%} of the ideal")

        # additional officers
        missing_hours = max(0, total_needed - actual)
        extra_officers = (missing_hours / 8).__ceil__()  
        print(f"To cover fully, you would need around {extra_officers} more officers")

        actual_hours = df['hours'].sum()
        
        max_officers   = num_officers     
        hours_per_off  = 2 * 4
        avail_hours    = max_officers * hours_per_off
        
        util_fraction  = actual_hours / avail_hours
        saved_hours    = avail_hours - actual_hours
        saved_officers = int((saved_hours / hours_per_off).__floor__())
        
        print(f"\nTotal hours assigned    : {actual_hours:.0f} h")
        print(f"Total hours available   : {avail_hours:.0f} h")
        print(f"Utilization rate        : {util_fraction:.1%}")
        print(f"Hours saved             : {saved_hours:.0f} h")
        print(f"Equivalent officers left: {saved_officers} out of {max_officers}")