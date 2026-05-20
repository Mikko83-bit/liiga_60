import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Player Finder",
    layout="wide"
)

st.title("Player Finder")

# =========================================================
# FILE UPLOADER
# =========================================================

uploaded_file = st.file_uploader(
    "Upload Liiga Excel File",
    type=["xlsx"]
)

if uploaded_file is None:

    st.info("Upload Excel file to continue.")
    st.stop()

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
# REMOVE BAD ROWS
# =========================================================

df = df.dropna(subset=["Time on ice"])

df = df[
    df["Time on ice"] > 0
]

# =========================================================
# SIDEBAR FILTERS
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
# AGE
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
# MIN TOI
# ---------------------------------------------------------

min_toi = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1000,
    value=200,
    step=10
)

# ---------------------------------------------------------
# MIN GAMES
# ---------------------------------------------------------

min_games = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=int(df["Games played"].max()),
    value=5
)

# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

profiles = [
    "Offensive Efficiency",
    "Playmaker",
    "Shooter",
    "Offensive Driver"
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
# DELTAS
# =========================================================

for metric in metrics:

    filtered_df[f"d_{metric}"] = (
        filtered_df[f"{metric}_per60"]
        - league_avg[metric]
    )

# =========================================================
# PROFILE WEIGHTS
# =========================================================

if selected_profile == "Offensive Efficiency":

    filtered_df["Score"] = (

        0.35 * filtered_df["d_Goals"]

        + 0.30 * filtered_df["d_First assist"]

        + 0.25 * filtered_df["d_xG"]

        + 0.15 * filtered_df["d_Shots"]

        + 0.15 * filtered_df["d_Passes to the slot"]

        + 0.10 * filtered_df["d_Pre-shots passes"]

        + 0.15 * filtered_df["d_Team xG when on ice"]

        - 0.10 * filtered_df["d_Opponent's xG when on ice"]

    )

elif selected_profile == "Playmaker":

    filtered_df["Score"] = (

        0.40 * filtered_df["d_First assist"]

        + 0.30 * filtered_df["d_Pre-shots passes"]

        + 0.30 * filtered_df["d_Passes to the slot"]

        + 0.15 * filtered_df["d_Team xG when on ice"]

        + 0.10 * filtered_df["d_xG"]

    )

elif selected_profile == "Shooter":

    filtered_df["Score"] = (

        0.40 * filtered_df["d_Goals"]

        + 0.35 * filtered_df["d_Shots"]

        + 0.30 * filtered_df["d_xG"]

    )

elif selected_profile == "Offensive Driver":

    filtered_df["Score"] = (

        0.35 * filtered_df["d_Team xG when on ice"]

        + 0.25 * filtered_df["d_xG"]

        + 0.20 * filtered_df["d_Passes to the slot"]

        + 0.20 * filtered_df["d_Pre-shots passes"]

        + 0.15 * filtered_df["d_First assist"]

        - 0.10 * filtered_df["d_Opponent's xG when on ice"]

    )

# =========================================================
# TOI FACTOR
# =========================================================

filtered_df["TOI Factor"] = (

    filtered_df["Time on ice"] / 600

).clip(0.50, 1.50)

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

    "Grade":
    filtered_df["Grade"],

    "Score":
    filtered_df["Final Score"].round(2),

    "Percentile":
    filtered_df["Percentile"].round(1),

    "Goals/60":
    filtered_df["Goals_per60"].round(2),

    "A1/60":
    filtered_df["First assist_per60"].round(2),

    "xG/60":
    filtered_df["xG_per60"].round(2),

    "Shots/60":
    filtered_df["Shots_per60"].round(2)

})

# =========================================================
# SHOW TABLE
# =========================================================

st.markdown(f"## {selected_profile}")

st.dataframe(
    output,
    use_container_width=True,
    height=850
)
