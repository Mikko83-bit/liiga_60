import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Defenseman Finder",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("Defenseman Finder")

st.markdown("""
Find defensemen with strong transition, puck-moving
and defensive underlying metrics.
""")

# =========================================================
# LOAD DATA
# =========================================================

FILE = "data/Liiga 2025-2026_skaters_teams.xlsx"

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
    "Breakouts",
    "Breakouts via pass",
    "Accurate passes, %",
    "Takeaways in DZ",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice",
    "OZ possession",
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
    "Breakouts",
    "Breakouts via pass",
    "Accurate passes, %",
    "Takeaways in DZ",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice",
    "OZ possession"
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
# ONLY DEFENSEMEN
# =========================================================

df = df[
    df["Position"] == "D"
]

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filters")

# ---------------------------------------------------------
# MAX AGE
# ---------------------------------------------------------

min_age = int(df["Age"].min())
max_age = int(df["Age"].max())

selected_age = st.sidebar.slider(
    "Maximum Age",
    min_value=min_age,
    max_value=max_age,
    value=max_age
)

# ---------------------------------------------------------
# MINIMUM TOI
# ---------------------------------------------------------

min_toi = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1500,
    value=300,
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

# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

profiles = [
    "Puck Moving",
    "Transition",
    "Two-Way",
    "Defensive"
]

selected_profile = st.sidebar.selectbox(
    "Profile",
    profiles
)

# =========================================================
# FILTER DATA
# =========================================================

filtered_df = df.copy()

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
    "Breakouts",
    "Breakouts via pass",
    "Accurate passes, %",
    "Takeaways in DZ",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice",
    "OZ possession"
]

negative_metrics = [
    "Puck losses",
    "Opponent's xG when on ice"
]

# =========================================================
# PER60
# =========================================================

per60_metrics = [
    "Breakouts",
    "Breakouts via pass",
    "Takeaways in DZ",
    "Puck losses"
]

for metric in per60_metrics:

    filtered_df[f"{metric}_per60"] = (
        filtered_df[metric]
        / filtered_df["Time on ice"]
    ) * 60

# =========================================================
# NON-PER60 METRICS
# =========================================================

filtered_df["Accurate passes, %_value"] = (
    filtered_df["Accurate passes, %"]
)

filtered_df["Team xG when on ice_value"] = (
    filtered_df["Team xG when on ice"]
)

filtered_df["Opponent's xG when on ice_value"] = (
    filtered_df["Opponent's xG when on ice"]
)

filtered_df["OZ possession_value"] = (
    filtered_df["OZ possession"]
)

# =========================================================
# CREATE ANALYTICS VALUE
# =========================================================

for metric in metrics:

    if metric in per60_metrics:

        filtered_df[f"{metric}_value"] = (
            filtered_df[f"{metric}_per60"]
        )

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

for metric in metrics:

    league_avg[metric] = (
        filtered_df[f"{metric}_value"].mean()
    )

# =========================================================
# DELTAS
# =========================================================

for metric in metrics:

    filtered_df[f"d_{metric}"] = (
        filtered_df[f"{metric}_value"]
        - league_avg[metric]
    )

# =========================================================
# PROFILE MODELS
# =========================================================

if selected_profile == "Puck Moving":

    filtered_df["Score"] = (

        0.35 * filtered_df["d_Breakouts via pass"]

        + 0.30 * filtered_df["d_Accurate passes, %"]

        + 0.20 * filtered_df["d_Breakouts"]

        + 0.15 * filtered_df["d_OZ possession"]

        - 0.10 * filtered_df["d_Puck losses"]

    )

elif selected_profile == "Transition":

    filtered_df["Score"] = (

        0.40 * filtered_df["d_Breakouts"]

        + 0.35 * filtered_df["d_Breakouts via pass"]

        + 0.20 * filtered_df["d_Team xG when on ice"]

        + 0.10 * filtered_df["d_Takeaways in DZ"]

    )

elif selected_profile == "Two-Way":

    filtered_df["Score"] = (

        0.25 * filtered_df["d_Breakouts"]

        + 0.20 * filtered_df["d_Breakouts via pass"]

        + 0.20 * filtered_df["d_Takeaways in DZ"]

        + 0.20 * filtered_df["d_Team xG when on ice"]

        - 0.25 * filtered_df["d_Opponent's xG when on ice"]

        - 0.10 * filtered_df["d_Puck losses"]

    )

elif selected_profile == "Defensive":

    filtered_df["Score"] = (

        0.35 * filtered_df["d_Takeaways in DZ"]

        - 0.35 * filtered_df["d_Opponent's xG when on ice"]

        - 0.20 * filtered_df["d_Puck losses"]

        + 0.15 * filtered_df["d_Accurate passes, %"]

        + 0.10 * filtered_df["d_Breakouts via pass"]

    )

# =========================================================
# TOI FACTOR
# =========================================================

filtered_df["TOI Factor"] = (

    filtered_df["Time on ice"] / 700

).clip(0.60, 1.50)

# =========================================================
# FINAL SCORE
# =========================================================

filtered_df["Final Score"] = (

    filtered_df["Score"]

    * filtered_df["TOI Factor"]

)

# =========================================================
# PERCENTILE
# =========================================================

filtered_df["Percentile"] = (
    filtered_df["Final Score"]
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
    "Final Score",
    ascending=False
)

filtered_df = filtered_df.reset_index(drop=True)

filtered_df.index += 1

# =========================================================
# OUTPUT
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

    "Grade":
    filtered_df["Grade"],

    "Score":
    filtered_df["Final Score"].round(2),

    "Breakouts/60":
    filtered_df["Breakouts_per60"].round(2),

    "Pass Breakouts/60":
    filtered_df["Breakouts via pass_per60"].round(2),

    "DZ Takeaways/60":
    filtered_df["Takeaways in DZ_per60"].round(2),

    "Puck Losses/60":
    filtered_df["Puck losses_per60"].round(2),

    "Pass %":
    filtered_df["Accurate passes, %"].round(1),

    "Team xG":
    filtered_df["Team xG when on ice"].round(2),

    "Opp xG":
    filtered_df["Opponent's xG when on ice"].round(2)

})

# =========================================================
# SHOW TABLE
# =========================================================

st.markdown(f"## {selected_profile} Defensemen")

st.dataframe(
    output,
    use_container_width=True,
    height=900
)
