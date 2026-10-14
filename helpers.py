"""Helper functions for the NEISS falls dashboard.

These use pandas only, so they can be tested without Streamlit.
"""
import pandas as pd

AGE_BINS = [65, 75, 85, 200]
AGE_LABELS = ["65-74", "75-84", "85+"]
ALL_LOCATIONS = "All locations"
DISPOSITION_ORDER = ["Treated and released", "Admitted/hospitalized", "Held for observation",
                     "Treated and transferred", "Fatality (incl. DOA/died in ER)"]

THEME_COLUMNS = {
    "theme_found_down": "Found down / unable to get up",
    "theme_dizzy": "Dizzy / fainted",
    "theme_dementia": "Dementia / confusion",
    "theme_bathroom": "Bathroom / toilet / shower",
    "theme_bed": "Bed / bedroom",
    "theme_walker": "Walker / cane / wheelchair",
    "theme_ladder_chair": "Ladder / chair / stool",
    "theme_slipped": "Slipped / wet / ice",
    "theme_stairs": "Stairs / steps",
    "theme_facility": "Nursing / assisted facility",
    "theme_tripped": "Tripped",
    "theme_outdoors": "Outdoors (curb / yard / porch)",
    "theme_pet": "Pet / dog",
    "theme_blood_thinner": "Blood thinner mentioned",
}


def load_data(path):
    """Read the dashboard CSV and add the age-group column."""
    df = pd.read_csv(path)
    df["age_group"] = pd.cut(df["age_years"], bins=AGE_BINS, right=False, labels=AGE_LABELS)
    return df


def filter_data(df, age_range, location):
    """Keep visits inside the age range (inclusive) and, unless ALL_LOCATIONS, at the chosen location."""
    out = df[(df["age_years"] >= age_range[0]) & (df["age_years"] <= age_range[1])]
    if location != ALL_LOCATIONS:
        out = out[out["location_label"] == location]
    return out


def population_label(age_range, location):
    """Plain-language description of the group, used to label charts."""
    ages = f"age {age_range[0]}" if age_range[0] == age_range[1] else f"ages {age_range[0]}-{age_range[1]}"
    if location == ALL_LOCATIONS:
        place = "any location"
    elif location == "Home":
        place = "at home"
    elif location == "Not recorded":
        place = "location not recorded"
    else:
        place = location.lower()
    return f"{ages}, {place}"


def headline(df):
    """Counts and percentages for the headline numbers."""
    n = len(df)
    if n == 0:
        return {"n": 0, "admitted_pct": float("nan"), "released_pct": float("nan"), "other_pct": float("nan")}
    admitted = int((df["disposition_label"] == "Admitted/hospitalized").sum())
    released = int((df["disposition_label"] == "Treated and released").sum())
    return {"n": n,
            "admitted_pct": admitted / n * 100,
            "released_pct": released / n * 100,
            "other_pct": (n - admitted - released) / n * 100}


def outcome_breakdown(df):
    """Visits and percent for each way the ED visit ended."""
    counts = df["disposition_label"].value_counts().reindex(DISPOSITION_ORDER, fill_value=0)
    out = counts.rename("visits").reset_index().rename(columns={"index": "outcome", "disposition_label": "outcome"})
    out["pct"] = out["visits"] / max(len(df), 1) * 100
    return out


def rate_by_group(df, column):
    """Admission rate (%) and number of visits for each value of `column`."""
    grouped = df.groupby(column, observed=True)["admitted"].agg(["mean", "size"])
    grouped["rate"] = grouped["mean"] * 100
    return grouped[["rate", "size"]].rename(columns={"size": "visits"})


def rate_by_age_and_sex(df):
    """Admission rate by age group for women and men (the 14 'not recorded' rows are left out)."""
    sub = df[df["sex_label"].isin(["Female", "Male"])]
    grouped = sub.groupby(["age_group", "sex_label"], observed=True)["admitted"].agg(["mean", "size"]).reset_index()
    grouped["rate"] = grouped["mean"] * 100
    return grouped.rename(columns={"size": "visits"})[["age_group", "sex_label", "rate", "visits"]]


def theme_table(df):
    """Prevalence and admission rate for each narrative theme."""
    rows = []
    for column, label in THEME_COLUMNS.items():
        hit = df[column] == 1
        visits = int(hit.sum())
        rows.append({"theme": label,
                     "visits": visits,
                     "share_of_visits_pct": visits / max(len(df), 1) * 100,
                     "admit_rate_pct": df.loc[hit, "admitted"].mean() * 100 if visits else float("nan"),
                     "admit_rate_without_pct": df.loc[~hit, "admitted"].mean() * 100 if (~hit).sum() else float("nan")})
    return pd.DataFrame(rows)


def sample_size_note(n):
    """Return (level, message) warning about small groups; level is None when the group is large enough."""
    if n < 30:
        return "error", f"Only {n} visits match, which is too few to say much. Treat these percentages as rough."
    if n < 100:
        return "warning", f"Only {n} visits match, so the percentages can move a lot with a few visits. Read them with caution."
    return None, ""
