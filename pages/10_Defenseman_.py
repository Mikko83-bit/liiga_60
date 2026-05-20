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
Compare defensemen using offensive, transition,
defensive and impact metrics.
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

    "Goals",
    "Points",
    "First assist",
    "xG",

    "Entries via pass",
    "Breakouts via pass",

    "Takeaways in DZ",
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

# =========================================================
# APPLY FILTERS
# =========================================================

df = df[
    df["Time on ice"] >= MIN_TOI
]

df = df[
    df["Games played"] >= MIN_GP
]

# =========================================================
# TEAMS
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

# =========================================================
# PLAYERS
# =========================================================

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
    "Goals",
    "Points",
    "First assist",
    "xG",
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
# METRICS
# =========================================================

metrics = {

    "Goals":
    "Goals_per60",

    "Points":
    "Points_per60",

    "First assist":
    "First assist_per60",

    "xG":
    "xG_per60",

    "Entries via pass":
    "Entries via pass_per60",

    "Breakouts via pass":
    "Breakouts via pass_per60",

    "DZ Takeaways":
    "Takeaways in DZ_per60",

    "Puck losses":
    "Puck losses_per60",

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
# CLEAN NaN / INF
# =========================================================

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df = df.fillna(0)

# =========================================================
# PERCENTILES
# =========================================================

for display_name, metric_col in metrics.items():

    if display_name in reverse_metrics:

        df[f"{display_name}_pct"] = (
            df[metric_col]
            .rank(
                pct=True,
                ascending=False
            )
        ) * 100

    else:

        df[f"{display_name}_pct"] = (
            df[metric_col]
            .rank(
                pct=True
            )
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
# OVERALL DEFENSEMAN SCORE
# =========================================================

weights = {

    "Goals": 0.10,
    "Points": 0.10,
    "First assist": 0.10,
    "xG": 0.10,

    "Entries via pass": 0.15,
    "Breakouts via pass": 0.15,

    "DZ Takeaways": 0.10,

    "Team xG": 0.10,

    "Opp xG": 0.10
}

# =========================================================
# CALCULATE ALL SCORES
# =========================================================

all_scores = []

for _, row in df.iterrows():

    score = 0

    for metric, weight in weights.items():

        pct = row[f"{metric}_pct"] / 100

        score += pct * weight

    toi_factor = np.clip(
        row["Time on ice"] / 900,
        0.7,
        1.4
    )

    final_score = score * toi_factor

    all_scores.append(final_score)

df["Projection Score"] = all_scores

# =========================================================
# OVERALL PERCENTILE
# =========================================================

df["Overall Percentile"] = (
    df["Projection Score"]
    .rank(pct=True)
) * 100

# =========================================================
# REFRESH PLAYER DATA
# =========================================================

p1 = df[
    df["Player"] == player1
].iloc[0]

p2 = df[
    df["Player"] == player2
].iloc[0]

# =========================================================
# PLAYER SCORES
# =========================================================

p1_projection = round(
    p1["Projection Score"],
    2
)

p2_projection = round(
    p2["Projection Score"],
    2
)

p1_percentile = round(
    p1["Overall Percentile"],
    1
)

p2_percentile = round(
    p2["Overall Percentile"],
    1
)

p1_grade = round(
    4 + (p1_percentile / 100) * 6,
    1
)

p2_grade = round(
    4 + (p2_percentile / 100) * 6,
    1
)

p1_toi_factor = round(
    np.clip(
        p1["Time on ice"] / 900,
        0.7,
        1.4
    ),
    2
)

p2_toi_factor = round(
    np.clip(
        p2["Time on ice"] / 900,
        0.7,
        1.4
    ),
    2
)

# =========================================================
# HEADER
# =========================================================

left, right = st.columns(2)

with left:

    st.markdown(f"## {player1}")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Grade",
        p1_grade
    )

    c2.metric(
        "Projection",
        p1_projection
    )

    c3.metric(
        "Percentile",
        p1_percentile
    )

    c4.metric(
        "TOI Factor",
        p1_toi_factor
    )

with right:

    st.markdown(f"## {player2}")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Grade",
        p2_grade
    )

    c2.metric(
        "Projection",
        p2_projection
    )

    c3.metric(
        "Percentile",
        p2_percentile
    )

    c4.metric(
        "TOI Factor",
        p2_toi_factor
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

    height=700,

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

    # =====================================================
    # REVERSE LOGIC
    # =====================================================

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
    height=560
)
