"""Build the slim data file used by the dashboard.

Input : neiss2024_older_adult_falls.csv  (cleaned file saved by the notebook: adults 65+, fall narratives, known outcome)
Output: dashboard_data.csv               (fewer columns, small locations grouped, theme flags precomputed)

Run once:  python prepare_dashboard_data.py
"""
import pandas as pd

SOURCE = "neiss2024_older_adult_falls.csv"
TARGET = "dashboard_data.csv"

# Same keyword patterns as the notebook (Section 2.8). A narrative can match several themes.
THEMES = {
    "theme_found_down": r"\bFOUND (?:ON|DOWN|LYING|IN)\b|\bUNWITNESSED\b|\bUNABLE TO GET UP\b|\bLAY\b|\bLAID\b",
    "theme_dizzy": r"\bDIZZ\w*|\bSYNCOP\w*|\bPASSED OUT\b|\bBLACKED OUT\b|\bLIGHTHEAD\w*|\bFAINT\w*",
    "theme_dementia": r"\bDEMENTIA\b|\bALZHEIMER\w*|\bCONFUS\w*",
    "theme_bathroom": r"\bBATHROOM\b|\bTOILET\b|\bSHOWER\b|\bBATHTUB\b|\bTUB\b|\bCOMMODE\b",
    "theme_bed": r"\bBED\b|\bBEDROOM\b|\bMATTRESS\b|\bBEDSIDE\b",
    "theme_walker": r"\bWALKER\b|\bCANE\b|\bWHEELCHAIR\b|\bROLLATOR\b",
    "theme_ladder_chair": r"\bLADDER\b|\bCHAIR\b|\bSTOOL\b",
    "theme_slipped": r"\bSLIP(?:PED|S)?\b|\bWET\b|\bICE\b|\bICY\b|\bSNOW\b",
    "theme_stairs": r"\bSTAIRS?\b|\bSTEPS?\b|\bFLIGHT\b",
    "theme_facility": r"\bNURSING\b|\bASSISTED LIVING\b|\bSKILLED\b|\bFACILITY\b|\bLONG[- ]TERM\b|\bSNF\b|\bGROUP HOME\b",
    "theme_tripped": r"\bTRIPPED\b|\bTRIP\b|\bTRIPPING\b",
    "theme_outdoors": r"\bCURB\b|\bSIDEWALK\b|\bPARKING\b|\bDRIVEWAY\b|\bYARD\b|\bPORCH\b",
    "theme_pet": r"\bDOG\b|\bCAT\b|\bPET\b",
    "theme_blood_thinner": r"\bBLOOD THINNERS?\b|\bELIQUIS\b|\bCOUMADIN\b|\bWARFARIN\b|\bXARELTO\b|\bANTICOAGULAT\w*|\bPLAVIX\b|\bAPIXABAN\b",
}
SMALL_LOCATIONS = ["Farm/ranch", "Industrial", "Mobile/manufactured home", "School/daycare"]  # each has fewer than 30 visits
SMALL_LABEL = "Other settings (farm, school, industrial, mobile home)"

df = pd.read_csv(SOURCE, dtype={"narrative_upper": str})
for column, pattern in THEMES.items():
    df[column] = df["narrative_upper"].str.contains(pattern, regex=True).astype(int)
df["location_label"] = df["location_label"].replace(SMALL_LOCATIONS, SMALL_LABEL)
df["serious"] = df["disposition_label"].isin(
    ["Treated and transferred", "Admitted/hospitalized", "Held for observation", "Fatality (incl. DOA/died in ER)"]).astype(int)
keep = ["case_number", "age_years", "sex_label", "location_label", "disposition_label", "admitted", "serious"] + list(THEMES)
df[keep].to_csv(TARGET, index=False)
print(f"Wrote {TARGET}: {len(df):,} rows, {len(keep)} columns")
