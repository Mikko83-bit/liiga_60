import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Projection Model",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("Projection Model")

st.markdown("""
Projection-oriented player model using:

- Relative production
- Team-adjusted impact
- Sustainable offensive metrics
- Usage-adjusted projection
""")

# =========================================================
# LOAD DATA
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# ---------------------------------------------------------
# SKATERS
# ---------------------------------------------------------

try:

    df = pd.read_excel(
        FILE,
        sheet_name="Skaters"
    )

except Exception as e:

    st.error(f"Failed loading Skaters sheet: {e}")
    st.stop()

# ---------------------------------------------------------
# TEAMS
# ---------------------------------------------------------

try:

    teams_df = pd.read_excel(
        FILE,
        sheet_name="Teams"
    )

except Exception as e:

    st.error(f"Failed loading Teams sheet: {e}")
    st.stop()

# =========================================================
# CLEAN COLUMN NAMES
# =========================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\r", "", regex=False)
)

teams_df.columns = (
    teams_df.columns
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\r", "", regex=False)
)

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_player_columns = [

    "Player",
    "Team",
    "Position",

    "Date of birth",

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

required_team_columns = [

    "Team",
    "Games",

    "xGF",
    "xGA"
]

# =========================================================
# CHECK PLAYER COLUMNS
# =========================================================

missing_player_cols = [

    col for col in required_player_columns
    if col not in df.columns
]

if len(missing_player_cols) > 0:

    st.error(
        f"Missing player columns: {missing_player_cols}"
    )

    st.write(df.columns.tolist())

    st.stop()

# =========================================================
# CHECK TEAM COLUMNS
# =========================================================

missing_team_cols = [

    col for col in required_team_columns
    if col not in teams_df.columns
]

if len(missing_team_cols) > 0:

    st.error(
        f"Missing team columns: {missing_team_cols}"
    )

    st.write(teams_df.columns.tolist())

    st.stop()

# =========================================================
# NUMERIC CONVERSION
# =========================================================

player_numeric_cols = [

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

for col in player_numeric_cols:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

team_numeric_cols = [

    "Games",
    "xGF",
    "xGA"
]

for col in team_numeric_cols:

    teams_df[col] = pd.to_numeric(
        teams_df[col],
        errors="coerce"
    )

# =========================================================
# AGE
# =========================================================

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

# =========================================================
# CLEAN DATA
# =========================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

# ONLY NUMERIC COLUMNS
fill_cols = [

    "Goals",
    "First assist",

    "xG",

    "Pre-shots passes",

    "Puck losses",

    "Team xG when on ice",
    "Opponent's xG when on ice",

    "Games played",
    "Time on ice",

    "Age"
]

df[fill_cols] = df[fill_cols].fillna(0)

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
# MIN TOI
# ---------------------------------------------------------

min_toi = st.sidebar.slider(
    "Minimum TOI",
    0,
    2000,
    300,
    10
)

# ---------------------------------------------------------
# MIN GP
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
# PER60
# =========================================================

per60_metrics = [

    "Goals",
    "First assist",

    "xG",

    "Pre-shots passes",

    "Puck losses"
]

for metric in per60_metrics:

    df[f"{metric}_per60"] = (

        df[metric]

        / df["Time on ice"]

    ) * 60

# =========================================================
# TEAM CONTEXT
# =========================================================

teams_df["xGF_per_game"] = (

    teams_df["xGF"]

    / teams_df["Games"]
)

teams_df["xGA_per_game"] = (

    teams_df["xGA"]

    / teams_df["Games"]
)

# =========================================================
# TEAM MAPS
# =========================================================

team_xgf_map = dict(

    zip(
        teams_df["Team"],
        teams_df["xGF_per_game"]
    )
)

team_xga_map = dict(

    zip(
        teams_df["Team"],
        teams_df["xGA_per_game"]
    )
)

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

league_metrics = [

    "Goals_per60",

    "First assist_per60",

    "xG_per60",

    "Pre-shots passes_per60",

    "Puck losses_per60"
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

df["dPreShots"] = (

    df["Pre-shots passes_per60"]

    - league_avg["Pre-shots passes_per60"]
)

# =========================================================
# REVERSE PUCK LOSSES
# =========================================================

df["dPuckLoss"] = (

    league_avg["Puck losses_per60"]

    - df["Puck losses_per60"]
)

# =========================================================
# RELATIVE TEAM IMPACT
# =========================================================

df["Rel xGF"] = (

    df["Team xG when on ice"]

    - df["Team"].map(team_xgf_map)
)

df["Rel xGA"] = (

    df["Team"].map(team_xga_map)

    - df["Opponent's xG when on ice"]
)

# =========================================================
# PROJECTION SCORE
# =========================================================

df["Projection Raw"] = (

    (0.22 * df["dGoals"])

    + (0.28 * df["dA1"])

    + (0.22 * df["dxG"])

    + (0.18 * df["dPreShots"])

    + (0.12 * df["Rel xGF"])

    + (0.12 * df["Rel xGA"])

    + (0.06 * df["dPuckLoss"])
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
# FINAL SCORE
# =========================================================

df["Projection Score"] = (

    df["Projection Raw"]

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
# DISPLAY
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

    "Rel xGF",

    "Rel xGA"
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

    "Rel xGF",

    "Rel xGA"
]

# =========================================================
# ROUNDING
# =========================================================

round_cols = [

    "Age",

    "TOI",

    "Projection",

    "Percentile",

    "Goals/60",

    "A1/60",

    "xG/60",

    "PreShots/60",

    "Rel xGF",

    "Rel xGA"
]

display_df[round_cols] = (
    display_df[round_cols]
    .round(2)
)

# =========================================================
# SHOW TABLE
# =========================================================

st.dataframe(
    display_df,
    use_container_width=True,
    height=900,
    hide_index=True
)
