# =========================================================
# SDHL / LIIGA PLAYER COMPARISON
# CLEAN HOCKEYSTATCARDS STYLE
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import os

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Player Comparison",
    page_icon="🏒",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.block-container{
    padding-top:2rem;
    max-width:1450px;
}

html, body, [class*="css"] {
    background-color:#030817;
    color:white;
    font-family:Arial;
}

/* remove top spacing */
div[data-testid="stVerticalBlock"]{
    gap:0.7rem;
}

/* sidebar */
section[data-testid="stSidebar"]{
    background:#111827;
}

/* metric cards */
.skill-card{
    border-radius:12px;
    padding:16px;
    text-align:center;
    margin-bottom:16px;
    height:105px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

/* title */
.main-title{
    font-size:52px;
    font-weight:900;
    margin-bottom:10px;
}

/* player names */
.player-name{
    font-size:32px;
    font-weight:800;
    margin-top:8px;
}

/* subtitle */
.player-sub{
    font-size:20px;
    color:#d1d5db;
    margin-bottom:20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.markdown(
    '<div class="main-title">🏒 SDHL Player Comparison</div>',
    unsafe_allow_html=True
)

# =========================================================
# FILE
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# =========================================================
# CLEAN COLUMNS
# =========================================================

def clean_columns(df):

    cols = []

    for col in df.columns:

        col = str(col)

        col = col.strip()

        col = col.replace(" ", "_")
        col = col.replace("/", "_")
        col = col.replace("%", "perc")
        col = col.replace("-", "_")
        col = col.replace("(", "")
        col = col.replace(")", "")
        col = col.replace(",", "")
        col = col.replace(".", "")
        col = col.replace("'", "")

        cols.append(col)

    df.columns = cols

    return df

# =========================================================
# PERCENTILE
# =========================================================

def percentile(series):

    return series.rank(pct=True) * 100

# =========================================================
# LABELS
# =========================================================

def get_label(value):

    if value >= 85:
        return "ELITE"

    elif value >= 70:
        return "EXCELLENT"

    elif value >= 55:
        return "GOOD"

    elif value >= 40:
        return "AVERAGE"

    return "BELOW AVG"

# =========================================================
# COLORS
# =========================================================

def get_color(value):

    if value >= 70:
        return "#3b82f6"

    elif value >= 40:
        return "#b7d3ea"

    return "#efb1b1"

# =========================================================
# LOGOS
# =========================================================

def get_logo(team):

    path = f"logos/{team}.png"

    if os.path.exists(path):

        return path

    return None

# =========================================================
# CARD
# =========================================================

def skill_card(skill, value):

    color = get_color(value)

    label = get_label(value)

    st.markdown(
        f"""
<div class="skill-card"
style="
background:{color};
color:black;
">

<div style="
font-size:16px;
font-weight:700;
margin-bottom:6px;
">
{skill}
</div>

<div style="
font-size:54px;
font-weight:900;
line-height:1;
">
{int(value)}
</div>

<div style="
font-size:13px;
font-weight:700;
letter-spacing:1px;
margin-top:5px;
">
{label}
</div>

</div>
""",
        unsafe_allow_html=True
    )

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_excel(FILE)

    df = clean_columns(df)

    # =====================================================
    # FIND GAMES COLUMN
    # =====================================================

    possible_games_cols = [

        "Games",
        "GP",
        "Games_played"

    ]

    games_col = None

    for col in possible_games_cols:

        if col in df.columns:

            games_col = col

            break

    if games_col:

        df["Games"] = pd.to_numeric(
            df[games_col],
            errors="coerce"
        ).fillna(0)

    else:

        df["Games"] = 0

    # =====================================================
    # NUMERIC
    # =====================================================

    numeric_cols = [

        "Goals",
        "Assists",
        "First_assist",
        "Shots",
        "Entries",
        "Breakouts",
        "Breakouts_via_pass",
        "Takeaways",
        "Puck_touches",
        "Puck_control_time",
        "Accurate_passes_perc",
        "Team_xG_when_on_ice",
        "Opponents_xG_when_on_ice",
        "NetxG",
        "CORSI_for_perc",
        "Fenwick_for_perc",
        "Time_on_ice"

    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        else:

            df[col] = 0

    # =====================================================
    # TOI
    # =====================================================

    df["TOI"] = df["Time_on_ice"]

    # =====================================================
    # PER60
    # =====================================================

    def per60(stat):

        return np.where(
            df["TOI"] > 0,
            (df[stat] / df["TOI"]) * 60,
            0
        )

    df["Goals60"] = per60("Goals")
    df["Assists60"] = per60("Assists")
    df["Shots60"] = per60("Shots")
    df["Entries60"] = per60("Entries")
    df["Breakouts60"] = per60("Breakouts")
    df["Takeaways60"] = per60("Takeaways")

    # =====================================================
    # xG
    # =====================================================

    df["xGF60"] = np.where(
        df["TOI"] > 0,
        (df["Team_xG_when_on_ice"] / df["TOI"]) * 60,
        0
    )

    df["xGA60"] = np.where(
        df["TOI"] > 0,
        (df["Opponents_xG_when_on_ice"] / df["TOI"]) * 60,
        0
    )

    # =====================================================
    # RAW SCORES
    # =====================================================

    df["ShootingRaw"] = (

        0.40 * df["Goals60"]

        +

        0.35 * df["Shots60"]

        +

        0.25 * df["xGF60"]

    )

    df["PlaymakingRaw"] = (

        0.50 * df["Assists60"]

        +

        0.30 * df["First_assist"]

        +

        0.20 * df["Accurate_passes_perc"]

    )

    df["TransitionRaw"] = (

        0.30 * df["Entries60"]

        +

        0.30 * df["Breakouts60"]

        +

        0.20 * df["Breakouts_via_pass"]

        +

        0.20 * df["Accurate_passes_perc"]

    )

    df["PuckMovementRaw"] = (

        0.50 * df["Puck_touches"]

        +

        0.50 * df["Puck_control_time"]

    )

    df["DefenseRaw"] = (

        0.50 * df["Takeaways60"]

        -

        0.50 * df["xGA60"]

    )

    df["ImpactRaw"] = (

        0.40 * df["NetxG"]

        +

        0.30 * df["CORSI_for_perc"]

        +

        0.30 * df["Fenwick_for_perc"]

    )

    # =====================================================
    # PERCENTILES
    # =====================================================

    categories = [

        "Shooting",
        "Playmaking",
        "Transition",
        "PuckMovement",
        "Defense",
        "Impact"

    ]

    for cat in categories:

        df[f"{cat}Score"] = percentile(
            df[f"{cat}Raw"]
        )

    return df

# =========================================================
# LOAD
# =========================================================

df = load_data()

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filters")

min_toi = st.sidebar.slider(
    "Minimum TOI",
    0,
    2000,
    200
)

min_games = st.sidebar.slider(
    "Minimum Games",
    0,
    60,
    5
)

position_filter = st.sidebar.selectbox(
    "Position",
    ["All", "F", "D"]
)

# =========================================================
# FILTERS
# =========================================================

filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["TOI"] >= min_toi
]

filtered_df = filtered_df[
    filtered_df["Games"] >= min_games
]

if position_filter != "All":

    filtered_df = filtered_df[
        filtered_df["Position"] == position_filter
    ]

# =========================================================
# TEAM FILTERS
# =========================================================

teams = sorted(
    filtered_df["Team"].dropna().unique()
)

team1 = st.sidebar.selectbox(
    "Team 1",
    teams
)

team2 = st.sidebar.selectbox(
    "Team 2",
    teams,
    index=min(1, len(teams)-1)
)

# =========================================================
# PLAYER FILTERS
# =========================================================

team1_df = filtered_df[
    filtered_df["Team"] == team1
]

team2_df = filtered_df[
    filtered_df["Team"] == team2
]

player1_name = st.sidebar.selectbox(
    "Player 1",
    sorted(team1_df["Player"].unique())
)

player2_name = st.sidebar.selectbox(
    "Player 2",
    sorted(team2_df["Player"].unique())
)

player1 = team1_df[
    team1_df["Player"] == player1_name
].iloc[0]

player2 = team2_df[
    team2_df["Player"] == player2_name
].iloc[0]

# =========================================================
# HEADER
# =========================================================

logo1 = get_logo(player1["Team"])
logo2 = get_logo(player2["Team"])

h1, h2, h3 = st.columns([5,1,5])

with h1:

    if logo1:

        st.image(
            logo1,
            width=95
        )

    st.markdown(
        f"""
<div class="player-name">
{player1['Player']}
</div>

<div class="player-sub">
{player1['Team']} | {player1['Position']}
</div>
""",
        unsafe_allow_html=True
    )

with h2:

    st.markdown("""
<div style="
font-size:54px;
font-weight:900;
text-align:center;
margin-top:70px;
">
VS
</div>
""", unsafe_allow_html=True)

with h3:

    if logo2:

        st.image(
            logo2,
            width=95
        )

    st.markdown(
        f"""
<div class="player-name">
{player2['Player']}
</div>

<div class="player-sub">
{player2['Team']} | {player2['Position']}
</div>
""",
        unsafe_allow_html=True
    )

# =========================================================
# SKILLS
# =========================================================

st.markdown("""
<div style="
font-size:32px;
font-weight:800;
margin-top:20px;
margin-bottom:20px;
">
Skill Comparison
</div>
""", unsafe_allow_html=True)

left, space, right = st.columns([5,1,5])

skills = [

    ("Shooting", "ShootingScore"),
    ("Playmaking", "PlaymakingScore"),
    ("Transition", "TransitionScore"),
    ("Puck Movement", "PuckMovementScore"),
    ("Defense", "DefenseScore"),
    ("Impact", "ImpactScore")

]

with left:

    for label, col in skills:

        skill_card(
            label,
            player1[col]
        )

with right:

    for label, col in skills:

        skill_card(
            label,
            player2[col]
        )
