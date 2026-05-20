import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Gs_projection",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("Projection Model")

st.markdown("""
Projection-oriented player model based on:

- Relative-to-league performance
- Usage-adjusted production
- Sustainable underlying metrics
""")

# =========================================================
# LOAD DATA
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

try:

    df = pd.read_excel(FILE)

except Exception as e:

    st.error(f"Excel loading failed: {e}")
    st.stop()

# =========================================================
# CLEAN COLUMNS
# =========================================================

df.columns = df.columns.str.strip()

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [

    "Player",
    "Team",
    "Position",

    "Games played",
    "Time on ice",

    "Goals",
    "First assist",
    "xG",

    "Pre-shots passes",

    "Team xG when on ice",
    "Opponent's xG when on ice",

    "Puck losses"
]

missing = [
    c for c in required_columns
    if c not in df.columns
]

if len(missing) > 0:

    st.error(f"Missing columns: {missing}")
    st.stop()

# =========================================================
# NUMERIC CONVERSION
# =========================================================

numeric_cols = required_columns[3:]

for col in numeric_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# =========================================================
# CLEAN NaN / INF
# =========================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.fillna(0)

# =========================================================
# AGE
# =========================================================

if "Date of birth" in df.columns:

    df["Date of birth"] = pd.to_datetime(
        df["Date of birth"],
        errors="coerce"
    )

    today = pd.Timestamp.today()

    df["Age"] = (
        (
            today - df["Date of birth"]
        ).dt.days / 365.25
    ).round(1)

else:

    df["Age"] = 25

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filters")

# ---------------------------------------------------------
# POSITION
# ---------------------------------------------------------

positions = sorted(
    df["Position"].dropna().unique()
)

selected_position = st.sidebar.selectbox(
    "Position",
    positions
)

# ---------------------------------------------------------
# MAX AGE
# ---------------------------------------------------------

selected_age = st.sidebar.slider(
    "Maximum Age",
    16,
    40,
    25
)

# ---------------------------------------------------------
# MINIMUM TOI
# ---------------------------------------------------------

min_toi = st.sidebar.slider(
    "Minimum TOI",
    0,
    2000,
    300,
    10
)

# ---------------------------------------------------------
# MINIMUM GAMES
# ---------------------------------------------------------

min_games = st.sidebar.slider(
    "Minimum Games",
    0,
    80,
    10
)

# =========================================================
# APPLY FILTERS
# =========================================================

df = df[
    df["Position"] == selected_position
]

df = df[
    df["Age"] <= selected_age
]

df = df[
    df["Time on ice"] >= min_toi
]

df = df[
    df["Games played"] >= min_games
]

# =========================================================
# STOP IF EMPTY
# =========================================================

if len(df) == 0:

    st.warning("No players found.")
    st.stop()

# =========================================================
# PER60 METRICS
# =========================================================

metrics_per60 = [

    "Goals",
    "First assist",
    "xG",
    "Pre-shots passes",
    "Puck losses"
]

for metric in metrics_per60:

    df[f"{metric}_per60"] = (
        df[metric]
        / df["Time on ice"]
    ) * 60

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

league_metrics = [

    "Goals_per60",
    "First assist_per60",
    "xG_per60",
    "Pre-shots passes_per60",
    "Puck losses_per60",

    "Team xG when on ice",
    "Opponent's xG when on ice"
]

for metric in league_metrics:

    league_avg[metric] = (
        df[metric].mean()
    )

# =========================================================
# DELTA ABOVE AVERAGE
# =========================================================

df["dGoals"] = (

    df["Goals_per60"]

    - league_avg["Goals_per60"]
)

df["dA1"] = (

    df["First assist_per60"]

    - league_avg["First assist_per60"]
)

df["dxG"] = (

    df["xG_per60"]

    - league_avg["xG_per60"]
)

df["dPreShot"] = (

    df["Pre-shots passes_per60"]

    - league_avg["Pre-shots passes_per60"]
)

# ---------------------------------------------------------
# REVERSE METRIC
# ---------------------------------------------------------

df["dPuckLoss"] = (

    league_avg["Puck losses_per60"]

    - df["Puck losses_per60"]
)

# ---------------------------------------------------------
# ON-ICE xG
# ---------------------------------------------------------

df["dxGF"] = (

    df["Team xG when on ice"]

    - league_avg["Team xG when on ice"]
)

# ---------------------------------------------------------
# REVERSE METRIC
# ---------------------------------------------------------

df["dxGA"] = (

    league_avg["Opponent's xG when on ice"]

    - df["Opponent's xG when on ice"]
)

# =========================================================
# PROJECTION SCORE
# =========================================================

df["Projection Score Raw"] = (

    (0.30 * df["dGoals"])

    + (0.30 * df["dA1"])

    + (0.20 * df["dxG"])

    + (0.15 * df["dxGF"])

    + (0.15 * df["dxGA"])

    + (0.12 * df["dPreShot"])

    + (0.08 * df["dPuckLoss"])
)

# =========================================================
# TOI FACTOR
# =========================================================

league_avg_toi = (
    df["Time on ice"].mean()
)

df["TOI Factor"] = np.sqrt(

    df["Time on ice"]

    / league_avg_toi
)

# =========================================================
# FINAL PROJECTION
# =========================================================

df["Projection Score"] = (

    df["Projection Score Raw"]

    * df["TOI Factor"]
)

# =========================================================
# PERCENTILE
# =========================================================

df["Percentile"] = (

    df["Projection Score"]

    .rank(pct=True)

) * 100

# =========================================================
# GRADE
# =========================================================

df["Grade"] = (

    4

    + (

        df["Percentile"]

        / 100

    ) * 6

).round(1)

# =========================================================
# SORT
# =========================================================

df = df.sort_values(
    "Projection Score",
    ascending=False
)

df = df.reset_index(drop=True)

df["Rank"] = df.index + 1

# =========================================================
# DISPLAY TABLE
# =========================================================

st.markdown("## Projection Rankings")

show_cols = [

    "Rank",

    "Player",
    "Team",
    "Age",

    "Games played",
    "Time on ice",

    "Grade",
    "Projection Score",
    "Percentile",

    "Goals_per60",
    "First assist_per60",
    "xG_per60",

    "Pre-shots passes_per60",

    "Team xG when on ice",
    "Opponent's xG when on ice"
]

display_df = df[show_cols].copy()

display_df.columns = [

    "Rank",

    "Player",
    "Team",
    "Age",

    "GP",
    "TOI",

    "Grade",
    "Projection",
    "Percentile",

    "Goals/60",
    "A1/60",
    "xG/60",

    "PreShots/60",

    "Team xG",
    "Opp xG"
]

# =========================================================
# ROUNDING
# =========================================================

numeric_round_cols = [

    "Age",
    "TOI",

    "Projection",
    "Percentile",

    "Goals/60",
    "A1/60",
    "xG/60",

    "PreShots/60",

    "Team xG",
    "Opp xG"
]

display_df[numeric_round_cols] = (
    display_df[numeric_round_cols]
    .round(2)
)

# =========================================================
# SHOW DATAFRAME
# =========================================================

st.dataframe(
    display_df,
    use_container_width=True,
    height=850,
    hide_index=True
)
