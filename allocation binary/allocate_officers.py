import numpy as np

WARD_TOTAL_HOURS = 800

def allocate_officers(merged):

    merged["allocation_weight"] = merged["forecast"] * 10 + merged["area_km2"]

    merged["officer_hours"] = 0.0

    for ward_code, group in merged.groupby("ward_code"):
        total_weight = group["allocation_weight"].sum()
        if total_weight == 0:
            continue

        raw_hours = (group["allocation_weight"] / total_weight) * WARD_TOTAL_HOURS
        hours_rounded = np.ceil(raw_hours / 2) * 2

        scale_factor = min(1.0, WARD_TOTAL_HOURS / hours_rounded.sum())
        final_hours = hours_rounded * scale_factor

        group_officers = np.ceil(final_hours / 8).astype(int)

        if group_officers.sum() > 100:
            officer_scale = 100 / group_officers.sum()
            final_hours = np.floor((final_hours * officer_scale) / 2) * 2
            group_officers = np.ceil(final_hours / 8).astype(int)

        merged.loc[group.index, "officer_hours"] = final_hours
        merged.loc[group.index, "officers"] = group_officers

    # Officers needed: officer_hours / 8 (2h/day × 4 days = 8h/week per officer)
    merged["officers"] = np.ceil(merged["officer_hours"] / 8).astype(int)

    return merged
