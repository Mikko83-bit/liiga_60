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
    "Entries",
    "Takeaways",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df = df.dropna(subset=["Time on ice"])

df = df[df["Time on ice"] > 0]

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")

# ---------------------------------------------------------
# MINIMUM TOI
# ---------------------------------------------------------

MIN_TOI = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1000,
    value=200,
    step=10
)

# ---------------------------------------------------------
# MINIMUM GAMES
# ---------------------------------------------------------

MIN_GAMES = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=int(df["Games played"].max()),
    value=5,
    step=1
)

# ---------------------------------------------------------
# APPLY MIN FILTERS
# ---------------------------------------------------------

df = df[
    (df["Time on ice"] >= MIN_TOI)
]

df = df[
    (df["Games played"] >= MIN_GAMES)
]

# ---------------------------------------------------------
# POSITION FILTER
# ---------------------------------------------------------

positions = sorted(
    df["Position"].dropna().unique()
)

selected_position = st.sidebar.selectbox(
    "Position",
    positions
)

df = df[
    df["Position"] == selected_position
]

# ---------------------------------------------------------
# TEAM FILTERS
# ---------------------------------------------------------

teams = sorted(
    df["Team"].dropna().unique()
)

team1 = st.sidebar.selectbox(
    "Team 1",
    teams,
    index=0
)

team2 = st.sidebar.selectbox(
    "Team 2",
    teams,
    index=min(1, len(teams)-1)
)

# ---------------------------------------------------------
# PLAYER FILTERS
# ---------------------------------------------------------

team1_players = sorted(
    df[df["Team"] == team1]["Player"].unique()
)

team2_players = sorted(
    df[df["Team"] == team2]["Player"].unique()
)

st.sidebar.markdown("---")

player1 = st.sidebar.selectbox(
    "Player 1",
    team1_players
)

player2 = st.sidebar.selectbox(
    "Player 2",
    team2_players
)

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

negative_metrics = [
    "Puck losses",
    "Opponent's xG when on ice"
]

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
# GRADE
# =========================================================

df["Grade"] = (
    4 + (df["Percentile"] / 100) * 6
).round(1)

# =========================================================
# METRIC PERCENTILES
# =========================================================

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
# PLAYER DATA
# =========================================================

p1 = df[
    df["Player"] == player1
].iloc[0]

p2 = df[
    df["Player"] == player2
].iloc[0]

# =========================================================
# PLAYER HEADER
# =========================================================

top1, top2 = st.columns(2)

with top1:

    st.markdown(f"## {player1}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Grade",
        p1["Grade"]
    )

    c2.metric(
        "Projection",
        round(
            p1["Projection Score"],
            2
        )
    )

    c3.metric(
        "Percentile",
        round(
            p1["Percentile"],
            1
        )
    )

with top2:

    st.markdown(f"## {player2}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Grade",
        p2["Grade"]
    )

    c2.metric(
        "Projection",
        round(
            p2["Projection Score"],
            2
        )
    )

    c3.metric(
        "Percentile",
        round(
            p2["Percentile"],
            1
        )
    )

# =========================================================
# SPIDER CHART
# =========================================================

fig = go.Figure()

# PLAYER 1
fig.add_trace(go.Scatterpolar(

    r=[
        p1[f"{m}_pct"]
        for m in metrics
    ],

    theta=metrics,

    fill='toself',

    name=player1,

    line=dict(
        color="#00E5FF",
        width=3
    ),

    fillcolor="rgba(0,229,255,0.30)"
))

# PLAYER 2
fig.add_trace(go.Scatterpolar(

    r=[
        p2[f"{m}_pct"]
        for m in metrics
    ],

    theta=metrics,

    fill='toself',

    name=player2,

    line=dict(
        color="#FF4B4B",
        width=3
    ),

    fillcolor="rgba(255,75,75,0.30)"
))

fig.update_layout(

    polar=dict(

        bgcolor="rgba(0,0,0,0)",

        radialaxis=dict(

            visible=True,

            range=[0, 100],

            tickfont=dict(
                size=10
            ),

            gridcolor="rgba(255,255,255,0.15)",

            linecolor="rgba(255,255,255,0.15)"
        ),

        angularaxis=dict(

            tickfont=dict(
                size=11
            ),

            gridcolor="rgba(255,255,255,0.10)",

            linecolor="rgba(255,255,255,0.10)"
        )
    ),

    showlegend=True,

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="center",
        x=0.5
    ),

    height=450,

    margin=dict(
        l=40,
        r=40,
        t=40,
        b=40
    ),

    paper_bgcolor="rgba(0,0,0,0)",

    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# UNDERLYING METRICS
# =========================================================

st.subheader("Underlying Metrics")

rows = []

for metric in metrics:

    p1_value = round(
        p1[f"{metric}_pct"],
        1
    )

    p2_value = round(
        p2[f"{metric}_pct"],
        1
    )

    # Better value indicator
    if p1_value > p2_value:

        p1_icon = "🟢"
        p2_icon = "🔴"

    elif p2_value > p1_value:

        p1_icon = "🔴"
        p2_icon = "🟢"

    else:

        p1_icon = "⚪"
        p2_icon = "⚪"

    rows.append({

        "Metric": metric,

        player1: f"{p1_icon} {p1_value}",

        player2: f"{p2_icon} {p2_value}"
    })

metric_table = pd.DataFrame(rows)

st.dataframe(
    metric_table,
    use_container_width=True,
    hide_index=True,
    height=420
)
