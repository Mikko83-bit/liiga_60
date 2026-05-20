import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Defenseman Comparison",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("Defenseman Comparison")

st.markdown("""
Compare defensemen using real underlying metrics.
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
    "Entries",
    "Breakouts",
    "Entries via pass",
    "Breakouts via pass",
    "Takeaways in DZ",
    "Puck losses",
    "Puck battles won, %",
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

numeric_columns = required_columns[4:]

for col in numeric_columns:

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

# =========================================================
# FILTER DEFENSEMEN
# =========================================================

df = df[
    df["Position"] == "D"
]

df = df.dropna(subset=["Time on ice"])

df = df[
    df["Time on ice"] > 0
]

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filters")

MIN_TOI = st.sidebar.slider(
    "Minimum TOI",
    0,
    1500,
    300,
    10
)

MIN_GP = st.sidebar.slider(
    "Minimum Games",
    0,
    int(df["Games played"].max()),
    10
)

df = df[
    df["Time on ice"] >= MIN_TOI
]

df = df[
    df["Games played"] >= MIN_GP
]

# =========================================================
# TEAM / PLAYER FILTERS
# =========================================================

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

players1 = sorted(
    df[
        df["Team"] == team1
    ]["Player"].unique()
)

players2 = sorted(
    df[
        df["Team"] == team2
    ]["Player"].unique()
)

st.sidebar.markdown("---")

player1 = st.sidebar.selectbox(
    "Player 1",
    players1
)

player2 = st.sidebar.selectbox(
    "Player 2",
    players2
)

# =========================================================
# PER60
# =========================================================

per60_metrics = [
    "Entries",
    "Breakouts",
    "Entries via pass",
    "Breakouts via pass",
    "Takeaways in DZ",
    "Puck losses"
]

for metric in per60_metrics:

    df[f"{metric}_per60"] = (
        df[metric]
        / df["Time on ice"]
    ) * 60

# =========================================================
# METRICS FOR DISPLAY
# =========================================================

metrics = {

    "Entries":
    "Entries_per60",

    "Breakouts":
    "Breakouts_per60",

    "Entries via pass":
    "Entries via pass_per60",

    "Breakouts via pass":
    "Breakouts via pass_per60",

    "DZ Takeaways":
    "Takeaways in DZ_per60",

    "Puck losses":
    "Puck losses_per60",

    "Battle win %":
    "Puck battles won, %",

    "Team xG":
    "Team xG when on ice",

    "Opp xG":
    "Opponent's xG when on ice"
}

# =========================================================
# REVERSE METRICS
# =========================================================

reverse_metrics = [
    "Puck losses",
    "Opp xG"
]

# =========================================================
# PERCENTILES
# =========================================================

for display_name, metric_col in metrics.items():

    if display_name in reverse_metrics:

        df[f"{display_name}_pct"] = (
            (
                df[metric_col].rank(
                    pct=True,
                    ascending=False
                )
            ) * 100
        )

    else:

        df[f"{display_name}_pct"] = (
            (
                df[metric_col].rank(
                    pct=True
                )
            ) * 100
        )

# =========================================================
# CLEAN
# =========================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.fillna(0)

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
# HEADER
# =========================================================

left, right = st.columns(2)

with left:

    st.markdown(f"## {player1}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "GP",
        int(p1["Games played"])
    )

    c2.metric(
        "TOI",
        int(p1["Time on ice"])
    )

    c3.metric(
        "Team",
        p1["Team"]
    )

with right:

    st.markdown(f"## {player2}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "GP",
        int(p2["Games played"])
    )

    c2.metric(
        "TOI",
        int(p2["Time on ice"])
    )

    c3.metric(
        "Team",
        p2["Team"]
    )

# =========================================================
# SPIDERWEB
# =========================================================

spider_metrics = list(metrics.keys())

fig = go.Figure()

# PLAYER 1

fig.add_trace(go.Scatterpolar(

    r=[
        p1[f"{m}_pct"]
        for m in spider_metrics
    ],

    theta=spider_metrics,

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
        for m in spider_metrics
    ],

    theta=spider_metrics,

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

        radialaxis=dict(
            visible=True,
            range=[0, 100]
        )
    ),

    showlegend=True,

    height=650,

    paper_bgcolor="rgba(0,0,0,0)",

    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# UNDERLYING METRICS TABLE
# =========================================================

st.markdown("## Underlying Metrics")

rows = []

for display_name, metric_col in metrics.items():

    p1_val = round(
        float(p1[metric_col]),
        2
    )

    p2_val = round(
        float(p2[metric_col]),
        2
    )

    p1_pct = round(
        float(p1[f"{display_name}_pct"]),
        0
    )

    p2_pct = round(
        float(p2[f"{display_name}_pct"]),
        0
    )

    # -----------------------------------------------------
    # REVERSE LOGIC
    # -----------------------------------------------------

    if display_name in reverse_metrics:

        if p1_val < p2_val:

            p1_icon = "🟢"
            p2_icon = "🔴"

        elif p2_val < p1_val:

            p1_icon = "🔴"
            p2_icon = "🟢"

        else:

            p1_icon = "⚪"
            p2_icon = "⚪"

    else:

        if p1_val > p2_val:

            p1_icon = "🟢"
            p2_icon = "🔴"

        elif p2_val > p1_val:

            p1_icon = "🔴"
            p2_icon = "🟢"

        else:

            p1_icon = "⚪"
            p2_icon = "⚪"

    rows.append({

        "Metric": display_name,

        player1:
        f"{p1_icon} {p1_val} ({int(p1_pct)}%)",

        player2:
        f"{p2_icon} {p2_val} ({int(p2_pct)}%)"
    })

table = pd.DataFrame(rows)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=520
)
