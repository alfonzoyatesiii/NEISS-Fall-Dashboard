"""Falls in Older Adults: interactive dashboard (NEISS 2024).

Run locally:   streamlit run app.py
"""
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from helpers import (AGE_LABELS, ALL_LOCATIONS, filter_data, headline, load_data, outcome_breakdown,
                     population_label, rate_by_age_and_sex, rate_by_group, sample_size_note, theme_table)

DATA_PATH = Path(__file__).parent / "dashboard_data.csv"
BLUE, ORANGE, GRAY, PURPLE, GREEN = "#4682b4", "#e07b00", "#8a8a8a", "#7b3f98", "#2e8b57"

st.set_page_config(page_title="Falls in Older Adults (NEISS 2024)", layout="wide", initial_sidebar_state="expanded")

# Make the built-in open/close arrow for the sidebar easier to see (selectors cover older and newer Streamlit versions).
st.markdown(
    """
    <style>
    [data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"],
    [data-testid="collapsedControl"] button, [data-testid="stSidebarCollapsedControl"] button {
        background: #fdecea; border: 2px solid #c0392b; border-radius: 8px; color: #c0392b;
    }
    [data-testid="stSidebarCollapseButton"] button:hover, [data-testid="stExpandSidebarButton"]:hover {
        background: #f8c9c4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def get_data():
    """Load the dashboard data once and reuse it between interactions."""
    return load_data(DATA_PATH)


df = get_data()
n_all = len(df)
base_admit = df["admitted"].mean() * 100

# ---------------------------------------------------------------- sidebar: the interaction
st.sidebar.caption("Tip: close this panel with the « arrow at its top right for a wider view of the charts.")
st.sidebar.header("Choose a group of ED fall visits")
age_range = st.sidebar.slider("Age range (years)", min_value=65, max_value=110, value=(65, 110), step=1,
                              help="Set both ends to the same number to look at one age.")
location_options = [ALL_LOCATIONS] + df["location_label"].value_counts().index.tolist()
location = st.sidebar.selectbox("Where the fall happened", location_options,
                                help="The incident location the hospital recorded. 'Not recorded' means it was left blank. 'Other public property' includes many care-facility falls: about half of its notes mention a nursing or assisted-living facility.")
selection = filter_data(df, age_range, location)
group_label = population_label(age_range, location)
st.sidebar.markdown(f"**{len(selection):,}** of {n_all:,} visits match.")
st.sidebar.info(
    "**How to read the percentages.** They show how often ED fall visits *like this one* ended in admission in the 2024 data. "
    "They are **not** a personal risk prediction: everyone in the data already went to an ED after a fall, and "
    "falls that never reach an ED are missing."
)
st.sidebar.caption("Source: U.S. CPSC NEISS 2024. Counts are visits in the sample, not national totals.")

# ---------------------------------------------------------------- header
st.title("Falls in older adults: which visits end in the hospital?")
st.markdown(
    f"**{n_all:,} emergency-department (ED) visits in 2024** for falls by adults 65 and older "
    "(U.S. CPSC injury surveillance data). Use the panel on the left to choose a group of visits."
)
st.caption("Want more room for the charts? Close the left panel with the « arrow at its top right, and reopen it with the » arrow at the top left.")

if selection.empty:
    st.warning(f"No ED fall visits match **{group_label}**. Try a wider age range or choose 'All locations'.")
    st.stop()

tab_group, tab_compare, tab_text, tab_findings = st.tabs(
    ["Your selection", "How groups compare", "What the narratives say", "Findings and limits"])

# ---------------------------------------------------------------- tab 1: your selection
with tab_group:
    st.subheader(f"ED fall visits: {group_label}")
    head = headline(selection)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ED fall visits in this group", f"{head['n']:,}")
    c2.metric("Admitted to the hospital", f"{head['admitted_pct']:.1f}%",
              delta=f"{head['admitted_pct'] - base_admit:+.1f} points vs. all fall visits ({base_admit:.1f}%)", delta_color="off")
    c3.metric("Treated and released", f"{head['released_pct']:.1f}%")
    c4.metric("Other outcomes", f"{head['other_pct']:.1f}%",
              help="Held for observation, transferred to another hospital, or died in the ED.")
    st.markdown(
        f"**In plain words:** of every 100 ED fall visits like this, about **{head['admitted_pct']:.0f}** ended in "
        f"hospital admission and about **{head['released_pct']:.0f}** were treated and released."
    )
    level, message = sample_size_note(head["n"])
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)

    left, right = st.columns(2)
    with left:
        breakdown = outcome_breakdown(selection)
        fig = go.Figure(go.Bar(
            x=breakdown["pct"], y=breakdown["outcome"], orientation="h", marker_color=BLUE,
            text=[f"{p:.1f}% (n={v:,})" for p, v in zip(breakdown["pct"], breakdown["visits"])], textposition="outside"))
        fig.update_layout(title="How the ED visit ended", xaxis_title="Share of visits in this group (%)", yaxis_title="",
                          xaxis_range=[0, 100], yaxis_autorange="reversed", height=380, margin=dict(l=10, r=10, t=50, b=40))
        st.plotly_chart(fig)
        st.caption(f"Population: {group_label} ({len(selection):,} visits).")
    with right:
        location_df = filter_data(df, (65, 110), location)
        ages = location_df.loc[location_df["age_years"] <= 100, "age_years"]
        fig = go.Figure(go.Histogram(x=ages, xbins=dict(start=65, end=101, size=1), marker_color=BLUE))
        fig.add_vrect(x0=age_range[0] - 0.5, x1=min(age_range[1], 100) + 0.5, fillcolor=ORANGE, opacity=0.25, line_width=0)
        fig.update_layout(title="Age of older adults treated for a fall", xaxis_title="Age in years (axis stops at 100)",
                          yaxis_title="Number of ED visits", height=380, margin=dict(l=10, r=10, t=50, b=40), bargap=0.05)
        st.plotly_chart(fig)
        place = "all locations" if location == ALL_LOCATIONS else location
        st.caption(f"Population: all ages 65+ at {place} ({len(location_df):,} visits). The orange band is your age range.")

# ---------------------------------------------------------------- tab 2: compare groups
with tab_compare:
    st.subheader("How admission rates differ between groups")
    left, right = st.columns(2)
    with left:
        location_df = filter_data(df, (65, 110), location)
        by_sex = rate_by_age_and_sex(location_df)
        fig = go.Figure()
        for sex, colour in [("Female", PURPLE), ("Male", GREEN)]:
            part = by_sex[by_sex["sex_label"] == sex].set_index("age_group").reindex(AGE_LABELS)
            fig.add_trace(go.Bar(
                name=sex, x=AGE_LABELS, y=part["rate"].tolist(), marker_color=colour,
                text=[f"{r:.1f}%<br>n={int(v):,}" if v == v else "" for r, v in zip(part["rate"], part["visits"])],
                textposition="outside"))
        fig.update_layout(barmode="group", title="Admission rate by age group and sex", xaxis_title="Age group (years)",
                          yaxis_title="Admitted (% of fall visits)", yaxis_range=[0, 60], height=420,
                          margin=dict(l=10, r=10, t=50, b=40), legend_title_text="Sex")
        st.plotly_chart(fig)
        place = "all locations" if location == ALL_LOCATIONS else location
        st.caption(f"Population: all ages 65+ at {place} ({len(location_df):,} visits). The age filter is not applied because this chart already splits by age group.")
    with right:
        age_df = filter_data(df, age_range, ALL_LOCATIONS)
        by_location = rate_by_group(age_df, "location_label")
        by_location = by_location[by_location["visits"] >= 100].sort_values("rate")
        if by_location.empty:
            st.info("No location has at least 100 visits in this age range, so the chart is hidden.")
        else:
            colours = [ORANGE if name == location else BLUE for name in by_location.index]
            fig = go.Figure(go.Bar(
                x=by_location["rate"], y=by_location.index.tolist(), orientation="h", marker_color=colours,
                text=[f"{r:.1f}% (n={int(v):,})" for r, v in zip(by_location["rate"], by_location["visits"])], textposition="outside"))
            fig.add_vline(x=age_df["admitted"].mean() * 100, line_dash="dash", line_color=GRAY,
                          annotation_text="All locations", annotation_position="top")
            fig.update_layout(title="Admission rate by where the fall happened", xaxis_title="Admitted (% of fall visits)",
                              yaxis_title="", xaxis_range=[0, 55], height=420, margin=dict(l=10, r=10, t=50, b=40))
            st.plotly_chart(fig)
            st.caption(f"Population: {population_label(age_range, ALL_LOCATIONS)} ({len(age_df):,} visits). "
                       "Locations with fewer than 100 visits are hidden. Your chosen location is orange.")

# ---------------------------------------------------------------- tab 3: narratives
with tab_text:
    st.subheader("What the hospital narratives describe")
    st.markdown(
        "Each ED visit has a short note describing how the fall happened. I searched those notes for common situations "
        "(a note can match more than one). The chart shows how often visits mentioning each situation ended in admission."
    )
    use_selection = st.checkbox("Apply my age and location selection to this chart", value=False)
    theme_df = selection if use_selection else df
    theme_label = f"{group_label}" if use_selection else "all ages 65+, all locations"
    themes = theme_table(theme_df)
    themes = themes[themes["visits"] >= 30].sort_values("admit_rate_pct")
    theme_base = theme_df["admitted"].mean() * 100
    if themes.empty:
        st.info("Fewer than 30 visits mention any situation in this group, so the chart is hidden. Try a wider selection.")
    else:
        fig = go.Figure(go.Bar(
            x=themes["admit_rate_pct"], y=themes["theme"], orientation="h", marker_color=BLUE,
            text=[f"{r:.0f}% (n={int(v):,}; {s:.0f}% of visits)" for r, v, s in
                  zip(themes["admit_rate_pct"], themes["visits"], themes["share_of_visits_pct"])], textposition="outside"))
        fig.add_vline(x=theme_base, line_dash="dash", line_color=ORANGE,
                      annotation_text=f"All visits in this group: {theme_base:.1f}%", annotation_position="top")
        fig.update_layout(title="Admission rate for visits that mention each situation", xaxis_title="Admitted (% of visits mentioning it)",
                          yaxis_title="", xaxis_range=[0, 75], height=560, margin=dict(l=10, r=10, t=50, b=40))
        st.plotly_chart(fig)
        st.caption(f"Population: {theme_label} ({len(theme_df):,} visits). Situations with fewer than 30 visits are hidden. "
                   "Keyword matching is imperfect and situations overlap.")
    st.markdown("**Examples from the notes** (shortened; numbers are CPSC case numbers)")
    with st.expander("Bed and bathroom falls"):
        st.markdown('- "FELL WHILE HE WAS WALKING TO THE BATHROOM" [241160357], admitted\n'
                    '- "TRIED TO GET OUT OF BED & TRIPPED OVER BLANKETS" [240846036], treated and released\n'
                    '- "WALKING AROUND IN THE DARK IN THE MIDDLE OF THE NIGHT" [240181492], admitted')
    with st.expander("Dizziness, weakness and being found down"):
        st.markdown('- "FELT LIGHTHEADED AND DIZZY AND THEN FELL BACKWARDS" [241281577], admitted\n'
                    '- "FELL ON THE FLOOR & WAS UNABLE TO GET UP. DOWN OVERNIGHT TIL FOUND" [250260398], admitted\n'
                    '- "FELL TO THE BATHROOM FLOOR LAID THERE FOR PROLONGED PERIOD" [240441386], admitted')
    with st.expander("Tripping on everyday hazards"):
        st.markdown('- "TRIPPED ON THE DOOR FRAME" [250237575], treated and released\n'
                    '- "TRIPPED ON HIS PANTS" [240434687], treated and released\n'
                    '- "STUMPED HER TOE ON THE CARPET" [240220967], treated and released')
    with st.expander("Examples that complicate the picture"):
        st.markdown('- "SLIPPED AND FELL IN SHOWER... DX: HEART FAILURE" [241026601], admitted. The admission diagnosis was an illness, not the fall injury.\n'
                    '- "SLIP AND FALL OVER FLIGHT OF STAIRS... FRACTURED HUMERUS" [240663977], treated and released.')

# ---------------------------------------------------------------- tab 4: findings and limits
with tab_findings:
    st.subheader("Main findings")
    st.caption("These use all 57,209 ED fall visits by adults 65+ and do not change with the filters.")
    st.markdown(
        "1. About one in three visits ended in admission (32.5%). Two in three were treated and released.\n"
        "2. Admission rises with age: 28% at ages 65-74, 33% at 75-84, and 37% at 85 and over.\n"
        "3. Falls at home ended in admission more often (35.7%) than falls on other public property (27.1%). About half of the "
        "'other public property' notes mention a nursing or assisted-living facility.\n"
        "4. Notes about dizziness or fainting (47%) and being found down or unable to get up (50%) were admitted most often."
    )
    st.subheader("Limits")
    st.markdown(
        "- Only people who reached an ED are included, so these are not rates of falling.\n"
        "- 'Admitted' can reflect an illness found during the visit. Patterns are not adjusted for age or health.\n"
        "- Notes are short and situations come from keyword searches. Groups under 100 visits are noisy."
    )
    st.caption("Source: U.S. CPSC NEISS 2024. Cleaning and analysis are in the project notebook.")
