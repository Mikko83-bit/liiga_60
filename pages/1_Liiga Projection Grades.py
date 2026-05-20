import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Liiga Projection Model",
    layout="wide"
)

st.title("Liiga Projection Grade Model")

st.write("""
Model logic:
1. Raw data
2. Per60 metrics
3. League-relative delta metrics
4. Weighted projection score
5. Percentile
6. Grade (4-10)
""")

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

    st.error(f"Missing columns: {missing_columns}")
    st.stop()

# =========================================================
# CLEAN DATA
# =========================================================

df = df.copy()

df["Time on ice"] = pd.to_numeric(
    df["Time on ice"],
    errors="coerce"
)

df = df.dropna(subset=["Time on ice"])

df = df[df["Time on ice"] > 0]

# =========================================================
# MINIMUM TOI
# =========================================================

MIN_TOI = st.sidebar.slider(
    "Minimum TOI",
    0,
    1000,
    200
)

df = df[df["Time on ice"] >= MIN_TOI]

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
# NUMERIC CONVERSION
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
# 4-10 GRADE
# =========================================================

df["Grade"] = (
    4 + (df["Percentile"] / 100) * 6
).round(1)

# =========================================================
# METRIC PERCENTILES
# =========================================================

negative_metrics = [
    "Puck losses",
    "Opponent's xG when on ice"
]

for metric in metrics:

    if metric in negative_metrics:

        df[f"{metric}_pct"] = (
            1 -
            df[f"{metric}_per60"].rank(pct=True)
        ) * 100

    else:

        df[f"{metric}_pct"] = (
            df[f"{metric}_per60"].rank(pct=True)
        ) * 100

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")

# Team filter
teams = sorted(df["Team"].dropna().unique())

selected_team = st.sidebar.selectbox(
    "Team",
    ["All Teams"] + teams
)

# Position filter
positions = sorted(df["Position"].dropna().unique())

selected_position = st.sidebar.selectbox(
    "Position",
    ["All Positions"] + positions
)

# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()

if selected_team != "All Teams":

    filtered_df = filtered_df[
        filtered_df["Team"] == selected_team
    ]

if selected_position != "All Positions":

    filtered_df = filtered_df[
        filtered_df["Position"] == selected_position
    ]

# =========================================================
# PLAYER SELECTORS
# =========================================================

players = sorted(filtered_df["Player"].unique())

player1 = st.selectbox(
    "Player 1",
    players,
    index=0
)

player2 = st.selectbox(
    "Player 2",
    players,
    index=min(1, len(players)-1)
)

p1 = filtered_df[
    filtered_df["Player"] == player1
].iloc[0]

p2 = filtered_df[
    filtered_df["Player"] == player2
].iloc[0]

# =========================================================
# PLAYER OVERVIEW
# =========================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader(player1)

    st.metric(
        "Grade",
        p1["Grade"]
    )

    st.metric(
        "Projection Score",
        round(
            p1["Projection Score"],
            2
        )
    )

    st.metric(
        "Percentile",
        round(
            p1["Percentile"],
            1
        )
    )

with col2:

    st.subheader(player2)

    st.metric(
        "Grade",
        p2["Grade"]
    )

    st.metric(
        "Projection Score",
        round(
            p2["Projection Score"],
            2
        )
    )

    st.metric(
        "Percentile",
        round(
            p2["Percentile"],
            1
        )
    )

# =========================================================
# SPIDER CHART
# =========================================================

spider_metrics = [
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

fig = go.Figure()

fig.add_trace(go.Scatterpolar(

    r=[
        p1[f"{m}_pct"]
        for m in spider_metrics
    ],

    theta=spider_metrics,

    fill='toself',

    name=player1
))

fig.add_trace(go.Scatterpolar(

    r=[
        p2[f"{m}_pct"]
        for m in spider_metrics
    ],

    theta=spider_metrics,

    fill='toself',

    name=player2
))

fig.update_layout(

    polar=dict(

        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),

    showlegend=True,

    height=800
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# UNDERLYING METRICS TABLE
# =========================================================

st.subheader("Underlying Metrics")

metric_table = pd.DataFrame({

    "Metric": spider_metrics,

    f"{player1} Per60": [

        round(
            p1[f"{m}_per60"],
            2
        )

        for m in spider_metrics
    ],

    f"{player2} Per60": [

        round(
            p2[f"{m}_per60"],
            2
        )

        for m in spider_metrics
    ],

    f"{player1} Percentile": [

        round(
            p1[f"{m}_pct"],
            1
        )

        for m in spider_metrics
    ],

    f"{player2} Percentile": [

        round(
            p2[f"{m}_pct"],
            1
        )

        for m in spider_metrics
    ]
})

st.dataframe(
    metric_table,
    use_container_width=True,
    height=600
)
