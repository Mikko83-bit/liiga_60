import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Breakout Finder",
    layout="wide"
)

st.title("Breakout Finder")

st.markdown("""
Find players with strong underlying metrics that may
predict future offensive breakout potential.
""")

# ==================================================
# LOAD DATA
# ==================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

df = pd.read_excel(FILE)
)
# =========================================================
# READ EXCEL
# =========================================================

try:

    df = pd.read_excel(uploaded_file)

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
    "Points",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Pre-shots passes",
    "Team xG when on ice",
    "Opponent's xG when on ice",
    "Date of birth"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if len(missing_columns) > 0:

    st.error(f"Missing columns: {missing_columns}")
    st.stop()

# =========================================================
# NUMERIC CONVERSION
# =========================================================

numeric_columns = [
    "Games played",
    "Time on ice",
    "Goals",
    "Points",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Pre-shots passes",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
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
    (today - df["Date of birth"]).dt.days / 365.25
).round(1)

# =========================================================
# CLEAN DATA
# =========================================================

df = df.dropna(subset=["Time on ice"])

df = df[
    df["Time on ice"] > 0
]

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

min_age = int(df["Age"].min())
max_age = int(df["Age"].max())

selected_age = st.sidebar.slider(
    "Maximum Age",
    min_value=min_age,
    max_value=max_age,
    value=23
)

# ---------------------------------------------------------
# MINIMUM TOI
# ---------------------------------------------------------

min_toi = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1000,
    value=250,
    step=10
)

# ---------------------------------------------------------
# MINIMUM GAMES
# ---------------------------------------------------------

min_games = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=int(df["Games played"].max()),
    value=10
)

# =========================================================
# FILTER DATA
# =========================================================

filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["Position"] == selected_position
]

filtered_df = filtered_df[
    filtered_df["Age"] <= selected_age
]

filtered_df = filtered_df[
    filtered_df["Time on ice"] >= min_toi
]

filtered_df = filtered_df[
    filtered_df["Games played"] >= min_games
]

# =========================================================
# METRICS
# =========================================================

metrics = [
    "Goals",
    "Points",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Pre-shots passes",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

negative_metrics = [
    "Opponent's xG when on ice"
]

# =========================================================
# PER60
# =========================================================

for metric in metrics:

    filtered_df[f"{metric}_per60"] = (
        filtered_df[metric]
        / filtered_df["Time on ice"]
    ) * 60

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

for metric in metrics:

    league_avg[metric] = (
        filtered_df[f"{metric}_per60"].mean()
    )

# =========================================================
# DELTA METRICS
# =========================================================

for metric in metrics:

    filtered_df[f"d_{metric}"] = (
        filtered_df[f"{metric}_per60"]
        - league_avg[metric]
    )

# =========================================================
# UNDERLYING SCORE
# =========================================================
# Strong process metrics
# =========================================================

filtered_df["Underlying Score"] = (

    0.30 * filtered_df["d_xG"]

    + 0.25 * filtered_df["d_Shots"]

    + 0.20 * filtered_df["d_Pre-shots passes"]

    + 0.20 * filtered_df["d_Passes to the slot"]

    + 0.15 * filtered_df["d_Team xG when on ice"]

    - 0.10 * filtered_df["d_Opponent's xG when on ice"]

)

# =========================================================
# PRODUCTION SCORE
# =========================================================

filtered_df["Production Score"] = (

    0.50 * filtered_df["d_Goals"]

    + 0.50 * filtered_df["d_Points"]

)

# =========================================================
# BREAKOUT GAP
# =========================================================
# Big positive gap:
# strong underlyings but lower production
# =========================================================

filtered_df["Breakout Gap"] = (

    filtered_df["Underlying Score"]

    - filtered_df["Production Score"]

)

# =========================================================
# AGE BONUS
# =========================================================

filtered_df["Age Bonus"] = (

    (23 - filtered_df["Age"]) * 0.08

).clip(0, 0.50)

# =========================================================
# TOI FACTOR
# =========================================================

filtered_df["TOI Factor"] = (

    filtered_df["Time on ice"] / 600

).clip(0.60, 1.40)

# =========================================================
# FINAL BREAKOUT SCORE
# =========================================================

filtered_df["Breakout Score"] = (

    (
        filtered_df["Breakout Gap"]

        + filtered_df["Underlying Score"]

        + filtered_df["Age Bonus"]
    )

    * filtered_df["TOI Factor"]

)

# =========================================================
# PERCENTILE
# =========================================================

filtered_df["Percentile"] = (
    filtered_df["Breakout Score"]
    .rank(pct=True)
) * 100

# =========================================================
# GRADE
# =========================================================

filtered_df["Grade"] = (
    4 +
    (
        filtered_df["Percentile"]
        / 100
    ) * 6
).round(1)

# =========================================================
# SORT
# =========================================================

filtered_df = filtered_df.sort_values(
    "Breakout Score",
    ascending=False
)

filtered_df = filtered_df.reset_index(drop=True)

filtered_df.index += 1

# =========================================================
# OUTPUT TABLE
# =========================================================

output = pd.DataFrame({

    "Rank":
    filtered_df.index,

    "Player":
    filtered_df["Player"],

    "Team":
    filtered_df["Team"],

    "Age":
    filtered_df["Age"],

    "GP":
    filtered_df["Games played"],

    "TOI":
    filtered_df["Time on ice"].round(0),

    "Breakout Grade":
    filtered_df["Grade"],

    "Breakout Score":
    filtered_df["Breakout Score"].round(2),

    "Underlying":
    filtered_df["Underlying Score"].round(2),

    "Production":
    filtered_df["Production Score"].round(2),

    "Gap":
    filtered_df["Breakout Gap"].round(2),

    "Goals/60":
    filtered_df["Goals_per60"].round(2),

    "Points/60":
    filtered_df["Points_per60"].round(2),

    "xG/60":
    filtered_df["xG_per60"].round(2),

    "Shots/60":
    filtered_df["Shots_per60"].round(2),

    "PreShot/60":
    filtered_df["Pre-shots passes_per60"].round(2)

})

# =========================================================
# SHOW TABLE
# =========================================================

st.markdown("## Breakout Candidates")

st.dataframe(
    output,
    use_container_width=True,
    height=900
)
