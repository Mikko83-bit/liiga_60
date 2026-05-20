import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Liiga Projection Grades",
    layout="wide"
)

st.title("Liiga Projection Grade Model")

st.write("""
Tämä malli:
- lukee Liiga Excel -datan
- laskee per60-luvut
- vertaa pelaajia liigakeskiarvoon
- muodostaa projection scoret
- muuntaa ne 4–10 arvosanoiksi
""")

# =========================================================
# FILE UPLOADER
# =========================================================

uploaded_file = st.file_uploader(
    "Upload Liiga Excel File",
    type=["xlsx"]
)

if uploaded_file is None:

    st.info("Upload your Excel file to continue.")
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
# CLEAN COLUMN NAMES
# =========================================================

df.columns = df.columns.str.strip()

# =========================================================
# SHOW COLUMNS
# =========================================================

with st.expander("Show Data Columns"):

    st.write(df.columns.tolist())

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "Player",
    "Time on ice",
    "Goals",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Entries",
    "Takeaways",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if len(missing_columns) > 0:

    st.error(
        f"Missing columns: {missing_columns}"
    )

    st.stop()

# =========================================================
# CLEAN DATA
# =========================================================

df = df.copy()

# Muunna TOI numeroksi
df["Time on ice"] = pd.to_numeric(
    df["Time on ice"],
    errors="coerce"
)

# Poista puuttuvat TOI-rivit
df = df.dropna(subset=["Time on ice"])

# Poista 0 TOI
df = df[df["Time on ice"] > 0]

# =========================================================
# METRICS
# =========================================================

metrics = [
    "Goals",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Entries",
    "Takeaways",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

# =========================================================
# CONVERT TO NUMERIC
# =========================================================

for metric in metrics:

    df[metric] = pd.to_numeric(
        df[metric],
        errors="coerce"
    ).fillna(0)

# =========================================================
# PER60
# =========================================================

for metric in metrics:

    df[f"{metric}_per60"] = (
        df[metric] / df["Time on ice"]
    ) * 60

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

for metric in metrics:

    league_avg[metric] = (
        df[f"{metric}_per60"].mean()
    )

# =========================================================
# DELTA METRICS
# =========================================================

for metric in metrics:

    df[f"d_{metric}"] = (
        df[f"{metric}_per60"]
        - league_avg[metric]
    )

# =========================================================
# PROJECTION SCORE
# =========================================================
# BASED ON RELATIVE PERFORMANCE
# =========================================================

df["Projection Score"] = (

    0.30 * df["d_Goals"]

    + 0.25 * df["d_First assist"]

    + 0.20 * df["d_xG"]

    + 0.10 * df["d_Passes to the slot"]

    + 0.10 * df["d_Entries"]

    + 0.10 * df["d_Takeaways"]

    - 0.15 * df["d_Puck losses"]

    + 0.20 * df["d_Team xG when on ice"]

    - 0.20 * df["d_Opponent's xG when on ice"]

)

# =========================================================
# PERCENTILE
# =========================================================

df["Percentile"] = (
    df["Projection Score"]
    .rank(pct=True)
) * 100

# =========================================================
# GRADE 4-10
# =========================================================

df["Grade"] = (
    4 + (df["Percentile"] / 100) * 6
).round(1)

# =========================================================
# SORT
# =========================================================

df = df.sort_values(
    by="Grade",
    ascending=False
)

# =========================================================
# PLAYER SELECT
# =========================================================

player = st.selectbox(
    "Select Player",
    sorted(df["Player"].unique())
)

player_df = df[
    df["Player"] == player
]

# =========================================================
# PLAYER OVERVIEW
# =========================================================

st.subheader(player)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Projection Score",
        round(
            player_df["Projection Score"].iloc[0],
            2
        )
    )

with col2:

    st.metric(
        "Percentile",
        round(
            player_df["Percentile"].iloc[0],
            1
        )
    )

with col3:

    st.metric(
        "Grade",
        player_df["Grade"].iloc[0]
    )

# =========================================================
# UNDERLYING METRICS
# =========================================================

st.subheader("Underlying Metrics")

metric_table = pd.DataFrame({

    "Metric": metrics,

    "Per60": [

        round(
            player_df[f"{m}_per60"].iloc[0],
            2
        )

        for m in metrics
    ],

    "Delta vs League": [

        round(
            player_df[f"d_{m}"].iloc[0],
            2
        )

        for m in metrics
    ]
})

st.dataframe(
    metric_table,
    use_container_width=True
)

# =========================================================
# ALL PLAYERS TABLE
# =========================================================

st.subheader("All Players")

table_columns = [
    "Player",
    "Projection Score",
    "Percentile",
    "Grade"
]

st.dataframe(
    df[table_columns],
    use_container_width=True,
    height=700
)
