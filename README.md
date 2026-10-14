# Falls in Older Adults: NEISS 2024 dashboard

Interactive Streamlit dashboard for the DESIGNTK 530 midterm project. It explores 57,209 emergency-department (ED) visits for falls by adults 65+ (U.S. CPSC NEISS, 2024).

## Run it
1. Install Python 3.10 or newer.
2. In this folder:
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. The dashboard opens at http://localhost:8501. Use the sidebar to pick an age range and a fall location.

## Files
| File | Purpose |
|---|---|
| `app.py` | The Streamlit dashboard |
| `helpers.py` | Data filtering and summary functions (pandas only) |
| `dashboard_data.csv` | Data the dashboard reads (57,209 rows) |
| `prepare_dashboard_data.py` | Rebuilds `dashboard_data.csv` from the notebook's cleaned file `neiss2024_older_adult_falls.csv` (put that file in this folder first) |
| `requirements.txt` | Python packages |

## Field guide for `dashboard_data.csv`
| Column | Meaning |
|---|---|
| `case_number` | CPSC case number (one ED visit) |
| `age_years` | Patient age in years (65 or older) |
| `sex_label` | Female, Male, or Not recorded |
| `location_label` | Where the fall happened, as recorded by the hospital. Farm/ranch, industrial, mobile home and school/daycare (63 visits in total) are grouped as "Other settings" |
| `disposition_label` | How the ED visit ended (treated and released, admitted, held for observation, transferred, died in the ED) |
| `admitted` | 1 if admitted/hospitalized, otherwise 0 |
| `serious` | 1 if admitted, transferred, held for observation, or died (the broader outcome in the notebook) |
| `theme_*` | 1 if the hospital narrative matches the keyword theme (for example `theme_bed`); keyword patterns are in `prepare_dashboard_data.py` |

## Source
U.S. Consumer Product Safety Commission, National Electronic Injury Surveillance System (NEISS), 2024 archived annual data: https://www.cpsc.gov/Research--Statistics/NEISS-Injury-Data
Visits are unweighted sample counts, not national estimates. The dashboard describes ED visits only, not personal risk.
