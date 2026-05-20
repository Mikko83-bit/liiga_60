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
Compare defensemen using role-based traits instead of
raw boxscore production.
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
    "First assist",
    "Entries",
    "Breakouts",
    "Entries via pass",
    "Breakouts via pass",
    "Takeaways",
    "Takeaways in DZ",
    "Puck losses",
    "Puck battles won, %",
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
    "Entries",
    "Breakouts",
    "Entries via pass",
    "Breakouts via pass",
    "Takeaways",
    "Takeaways in DZ",
    "Puck losses",
    "Puck battles won, %",
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
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")

MIN_TOI = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=1500,
    value=300,
    step=10
)

MIN_GP = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=int(df["Games played"].max()),
    value=10
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
# TEAMS / PLAYERS
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
# PER60 METRICS
# =========================================================

per60_metrics = [
    "Entries",
    "Breakouts",
    "Entries via pass",
    "Breakouts via pass",
    "Takeaways",
    "Takeaways in DZ",
    "Puck losses"
]

for metric in per60_metrics:

    df[f"{metric}_per60"] = (
        df[metric]
        / df["Time on ice"]
    ) * 60

# =========================================================
# TRAIT ENGINE
# =========================================================

# ---------------------------------------------------------
# TRANSITION
# ---------------------------------------------------------

df["Transition"] = (

    df["Entries_per60"]

    + df["Breakouts_per60"]

    + df["Entries via pass_per60"]

    + df["Breakouts via pass_per60"]

) / 4

# ---------------------------------------------------------
# PUCK MOVING
# ---------------------------------------------------------

df["Puck Moving"] = (

    df["Breakouts via pass_per60"]

    + df["Entries via pass_per60"]

    + df["Team xG when on ice"]

) / 3

# ---------------------------------------------------------
# DEFENSE
# ---------------------------------------------------------

opp_xg_reverse = (

    df["Opponent's xG when on ice"].max()

    - df["Opponent's xG when on ice"]

)

df["Defense"] = (

    df["Takeaways in DZ_per60"]

    + opp_xg_reverse

) / 2

# ---------------------------------------------------------
# PUCK SECURITY
# ---------------------------------------------------------

df["Puck Security"] = (

    df["Puck losses_per60"].max()

    - df["Puck losses_per60"]

)

# ---------------------------------------------------------
# PHYSICALITY
# ---------------------------------------------------------

df["Physicality"] = (
    df["Puck battles won, %"]
)

# ---------------------------------------------------------
# OFFENSIVE SUPPORT
# ---------------------------------------------------------

df["Offensive Support"] = (

    df["Goals"]

    + df["First assist"]

    + df["Team xG when on ice"]

) / 3

# =========================================================
# TRAITS
# =========================================================

traits = [
    "Transition",
    "Puck Moving",
    "Defense",
    "Puck Security",
    "Physicality",
    "Offensive Support"
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

for trait in traits:

    df[f"{trait}_pct"] = (
        df[trait]
        .rank(pct=True)
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
# HEADER
# =========================================================

left, right = st.columns(2)

with left:

    st.markdown(f"## {player1}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Age",
        p1["Age"]
    )

    c2.metric(
        "TOI",
        int(p1["Time on ice"])
    )

    c3.metric(
        "GP",
        int(p1["Games played"])
    )

with right:

    st.markdown(f"## {player2}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Age",
        p2["Age"]
    )

    c2.metric(
        "TOI",
        int(p2["Time on ice"])
    )

    c3.metric(
        "GP",
        int(p2["Games played"])
    )

# =========================================================
# SPIDERWEB
# =========================================================

fig = go.Figure()

# PLAYER 1

fig.add_trace(go.Scatterpolar(

    r=[
        p1[f"{trait}_pct"]
        for trait in traits
    ],

    theta=traits,

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
        p2[f"{trait}_pct"]
        for trait in traits
    ],

    theta=traits,

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

    height=550,

    paper_bgcolor="rgba(0,0,0,0)",

    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# UNDERLYING TRAITS TABLE
# =========================================================

st.markdown("## Underlying Traits")

rows = []

for trait in traits:

    p1_val = round(
        float(p1[trait]),
        2
    )

    p2_val = round(
        float(p2[trait]),
        2
    )

    p1_pct = round(
        float(p1[f"{trait}_pct"]),
        0
    )

    p2_pct = round(
        float(p2[f"{trait}_pct"]),
        0
    )

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

        "Trait": trait,

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
    height=420
)
