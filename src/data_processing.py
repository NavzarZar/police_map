import pandas as pd

def process_data(forecast_file, real_file, officer_hours=800, elasticity=-0.3, area_source="forecast"):

    # Read files
    forecast_df = pd.read_csv(forecast_file)
    real_df = pd.read_csv(real_file)


    # Merge and distinguish columns
    df = forecast_df.merge(real_df, on="lsoa_code", how="inner", suffixes=("_f", "_r"))


    area_col = "area_km2_f" if area_source == "forecast" else "area_km2_r"

    if area_col not in df.columns:
        raise KeyError("missing area km2 column, there is a problem somewhere")
    df = df.rename(columns={area_col: "area_km2"})

    for col in ["forecast", "observed", "area_km2"]:
        if col not in df.columns:
            raise KeyError("Missing a needed column")


    df["risk_density"] = df["forecast"] / df["area_km2"]
    df["base_density"] = officer_hours / df["area_km2"]

    total_risk = df["risk_density"].sum()

    df["allocated_hours"] = officer_hours * df["risk_density"] / total_risk

    df["new_density"] = df["allocated_hours"] / df["area_km2"]
    df["delta_density"] = (df["new_density"] - df["base_density"]) / df["base_density"]
                           
    df["predict_change_burglary"] = elasticity * df["delta_density"]
    df["prevented"] = df["predict_change_burglary"] * df["observed"]

    return df[["lsoa_code", "allocated_hours", "new_density", "prevented", "observed"]]
