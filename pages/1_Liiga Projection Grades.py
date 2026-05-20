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

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.metric-container {
    background-color: #111827;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
}

.metric-title {
    font-size: 15px;
    color: #9CA3AF;
}

.metric-value {
    font-size: 42px;
    font-weight: bold;
    color: white;
}

.metric-sub {
    font-size: 14px;
    color: #9CA3AF;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

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

    raw_df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(f"Excel loading failed: {e}")
    st.stop()

# =========================================================
# CLEAN COLUMNS
# =========================================================

raw_df.columns = raw_df.columns.str.strip()

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
    "Opponent's xG when on ice"
]

missing_columns = [
    col for col in required_columns
    if col not in raw_df.columns
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

    raw_df[col] = pd.to_numeric(
        raw_df[col],
        errors="coerce"
    )

raw_df = raw_df.dropna(subset=["Time on ice"])

raw_df = raw_df[
    raw_df["Time on ice"] > 0
]

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")

MIN_TOI = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1000,
    value=200,
    step=10
)

MIN_GAMES = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=int(raw_df["Games played"].max()),
    value=5,
    step=1
)

# =========================================================
# BASE ANALYTICS DATA
# =========================================================

base_df = raw_df.copy()

base_df = base_df[
    base_df["Time on ice"] >= MIN_TOI
]

base_df = base_df[
    base_df["Games played"] >= MIN_GAMES
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

    base_df[f"{metric}_per60"] = (
        base_df[metric]
        / base_df["Time on ice"]
    ) * 60

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

for metric in metrics:

    league_avg[metric] = (
        base_df[f"{metric}_per60"].mean()
    )

# =========================================================
# DELTA VS LEAGUE
# =========================================================

for metric in metrics:

    base_df[f"d_{metric}"] = (
        base_df[f"{metric}_per60"]
        - league_avg[metric]
    )

# =========================================================
# RAW DELTA PROJECTION MODEL
# =========================================================

base_df["Raw Projection"] = (

    0.35 * base_df["d_Goals"]

    + 0.30 * base_df["d_First assist"]

    + 0.22 * base_df["d_xG"]

    + 0.15 * base_df["d_Shots"]

    + 0.15 * base_df["d_Passes to the slot"]

    + 0.10 * base_df["d_Pre-shots passes"]

    + 0.15 * base_df["d_Team xG when on ice"]

    - 0.10 * base_df["d_Opponent's xG when on ice"]

)

# =========================================================
# TOI FACTOR
# =========================================================

base_df["TOI Factor"] = (

    base_df["Time on ice"] / 600

).clip(0.50, 1.50)

# =========================================================
# FINAL PROJECTION SCORE
# =========================================================

base_df["Projection Score"] = (

    base_df["Raw Projection"]

    * base_df["TOI Factor"]

)

# =========================================================
# PROJECTION PERCENTILE
# =========================================================

base_df["Projection Percentile"] = (
    base_df["Projection Score"]
    .rank(pct=True)
) * 100

# =========================================================
# GRADE
# =========================================================

base_df["Grade"] = (
    4 +
    (
        base_df["Projection Percentile"]
        / 100
    ) * 6
).round(1)

# =========================================================
# SPIDERWEB PERCENTILES
# =========================================================

for metric in metrics:

    if metric in negative_metrics:

        base_df[f"{metric}_pct"] = (
            1 -
            base_df[f"{metric}_per60"]
            .rank(pct=True)
        ) * 100

    else:

        base_df[f"{metric}_pct"] = (
            base_df[f"{metric}_per60"]
            .rank(pct=True)
        ) * 100

# =========================================================
# UI FILTERS
# =========================================================

positions = sorted(
    base_df["Position"].dropna().unique()
)

selected_position = st.sidebar.selectbox(
    "Position",
    positions
)

filtered_df = base_df[
    base_df["Position"] == selected_position
]

teams = sorted(
    filtered_df["Team"].dropna().unique()
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

team1_players = sorted(
    filtered_df[
        filtered_df["Team"] == team1
    ]["Player"].unique()
)

team2_players = sorted(
    filtered_df[
        filtered_df["Team"] == team2
    ]["Player"].unique()
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
# PLAYER DATA
# =========================================================

p1 = filtered_df[
    filtered_df["Player"] == player1
].iloc[0]

p2 = filtered_df[
    filtered_df["Player"] == player2
].iloc[0]

# =========================================================
# PLAYER HEADER
# =========================================================

top1, top2 = st.columns(2)

with top1:

    st.markdown(f"## {player1}")

    c1, c2, c3, c4 = st.columns(4)

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
            p1["Projection Percentile"],
            1
        )
    )

    c4.metric(
        "TOI Factor",
        round(
            p1["TOI Factor"],
            2
        )
    )

with top2:

    st.markdown(f"## {player2}")

    c1, c2, c3, c4 = st.columns(4)

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
            p2["Projection Percentile"],
            1
        )
    )

    c4.metric(
        "TOI Factor",
        round(
            p2["TOI Factor"],
            2
        )
    )

# =========================================================
# SPIDERWEB
# =========================================================

fig = go.Figure()

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

st.markdown("## Underlying Metrics")

rows = []

for metric in metrics:

    p1_per60 = round(
        p1[f"{metric}_per60"],
        2
    )

    p2_per60 = round(
        p2[f"{metric}_per60"],
        2
    )

    p1_pct = round(
        p1[f"{metric}_pct"]
    )

    p2_pct = round(
        p2[f"{metric}_pct"]
    )

    if metric in negative_metrics:

        if p1_per60 < p2_per60:

            p1_icon = "🟢"
            p2_icon = "🔴"

        elif p2_per60 < p1_per60:

            p1_icon = "🔴"
            p2_icon = "🟢"

        else:

            p1_icon = "⚪"
            p2_icon = "⚪"

    else:

        if p1_per60 > p2_per60:

            p1_icon = "🟢"
            p2_icon = "🔴"

        elif p2_per60 > p1_per60:

            p1_icon = "🔴"
            p2_icon = "🟢"

        else:

            p1_icon = "⚪"
            p2_icon = "⚪"

    rows.append({

        "Metric": metric,

        player1:
        f"{p1_icon} {p1_per60} ({p1_pct}%)",

        player2:
        f"{p2_icon} {p2_per60} ({p2_pct}%)"
    })

metric_table = pd.DataFrame(rows)

styled_table = metric_table.style.set_properties(**{
    'text-align': 'center',
    'font-size': '16px',
    'padding': '10px'
}).set_table_styles([
    {
        'selector': 'th',
        'props': [
            ('text-align', 'center'),
            ('font-size', '16px'),
            ('font-weight', 'bold')
        ]
    }
])

st.dataframe(
    styled_table,
    use_container_width=True,
    hide_index=True,
    height=470
)
