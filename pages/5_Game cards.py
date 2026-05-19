# =========================================================
# LIIGA PLAYER COMPARISON
# POSITION-ADJUSTED FINAL VERSION
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
import os

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Liiga Player Comparison",
    layout="wide"
)

# ==================================================
# LOAD DATA
# ==================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

df = pd.read_excel(FILE)

# ==================================================
# CLEAN DATA
# ==================================================

df.columns = (
    df.columns
    .str.strip()
    .str.replace(" ", "_")
    .str.replace("/", "_")
    .str.replace("%", "perc")
    .str.replace("-", "_")
    .str.replace("(", "", regex=False)
    .str.replace(")", "", regex=False)
    .str.replace(".", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.replace("'", "", regex=False)
)

# ==================================================
# NUMERIC COLUMNS
# ==================================================

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

# ==================================================
# GAMES COLUMN
# ==================================================

games_col = None

possible_games_cols = [

    "Games",
    "GP",
    "Games_played"

]

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

# ==================================================
# POSITION CLEAN
# ==================================================

df["Position"] = (
    df["Position"]
    .astype(str)
    .str.strip()
)

df["Team"] = (
    df["Team"]
    .astype(str)
    .str.strip()
)

# ==================================================
# TOI
# ==================================================

df["TOI"] = df["Time_on_ice"]

# ==================================================
# PER60
# ==================================================

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

# ==================================================
# XG
# ==================================================

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

# ==================================================
# RAW SCORES
# ==================================================

df["Shooting Raw"] = (

    0.40 * df["Goals60"]

    +

    0.35 * df["Shots60"]

    +

    0.25 * df["xGF60"]

)

df["Playmaking Raw"] = (

    0.50 * df["Assists60"]

    +

    0.30 * df["First_assist"]

    +

    0.20 * df["Accurate_passes_perc"]

)

df["Transition Raw"] = (

    0.30 * df["Entries60"]

    +

    0.30 * df["Breakouts60"]

    +

    0.20 * df["Breakouts_via_pass"]

    +

    0.20 * df["Accurate_passes_perc"]

)

df["Puck Movement Raw"] = (

    0.50 * df["Puck_touches"]

    +

    0.50 * df["Puck_control_time"]

)

df["Defense Raw"] = (

    0.50 * df["Takeaways60"]

    -

    0.50 * df["xGA60"]

)

df["Impact Raw"] = (

    0.40 * df["NetxG"]

    +

    0.30 * df["CORSI_for_perc"]

    +

    0.30 * df["Fenwick_for_perc"]

)

# ==================================================
# POSITIONAL PERCENTILES
# ==================================================

skill_categories = [

    "Shooting",
    "Playmaking",
    "Transition",
    "Puck Movement",
    "Defense",
    "Impact"

]

for skill in skill_categories:

    raw_col = f"{skill} Raw"

    score_col = f"{skill} Score"

    df[score_col] = (

        df.groupby("Position")[raw_col]
        .rank(pct=True) * 100

    )

# ==================================================
# POSITION-SPECIFIC OVERALL
# ==================================================

df["Overall Score"] = 0.0

# FORWARDS

forward_mask = df["Position"] == "F"

df.loc[forward_mask, "Overall Score"] = (

    df.loc[forward_mask, "Shooting Score"] * 0.25 +

    df.loc[forward_mask, "Playmaking Score"] * 0.25 +

    df.loc[forward_mask, "Transition Score"] * 0.25 +

    df.loc[forward_mask, "Puck Movement Score"] * 0.10 +

    df.loc[forward_mask, "Defense Score"] * 0.05 +

    df.loc[forward_mask, "Impact Score"] * 0.10

)

# DEFENSEMEN

defense_mask = df["Position"] == "D"

df.loc[defense_mask, "Overall Score"] = (

    df.loc[defense_mask, "Shooting Score"] * 0.10 +

    df.loc[defense_mask, "Playmaking Score"] * 0.15 +

    df.loc[defense_mask, "Transition Score"] * 0.25 +

    df.loc[defense_mask, "Puck Movement Score"] * 0.25 +

    df.loc[defense_mask, "Defense Score"] * 0.15 +

    df.loc[defense_mask, "Impact Score"] * 0.10

)

# ==================================================
# OVERALL PERCENTILE
# ==================================================

df["Overall Percentile"] = (

    df.groupby("Position")[
        "Overall Score"
    ].rank(pct=True) * 100

)

# ==================================================
# ROUND VALUES
# ==================================================

numeric = df.select_dtypes(include="number").columns

df[numeric] = df[numeric].round(1)

# ==================================================
# TEAM LOGOS
# ==================================================

def get_logo(team):

    path = os.path.join(
        "logos",
        f"{team}.png"
    )

    if os.path.exists(path):

        return path

    return None

# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Filters")

min_toi = st.sidebar.slider(
    "Minimum TOI",
    min_value=0,
    max_value=2000,
    value=200,
    step=10
)

min_games = st.sidebar.slider(
    "Minimum Games",
    min_value=0,
    max_value=60,
    value=5,
    step=1
)

# APPLY FILTERS

df = df[
    (df["TOI"] >= min_toi) &
    (df["Games"] >= min_games)
]

# ==================================================
# POSITION FILTER
# ==================================================

positions = sorted(
    df["Position"].dropna().unique()
)

selected_position = st.sidebar.selectbox(
    "Position",
    positions
)

filtered_df = df[
    df["Position"] == selected_position
]

# ==================================================
# TEAM FILTERS
# ==================================================

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

# ==================================================
# PLAYER FILTERS
# ==================================================

team1_players = sorted(
    filtered_df[
        filtered_df["Team"] == team1
    ]["Player"].dropna().unique()
)

team2_players = sorted(
    filtered_df[
        filtered_df["Team"] == team2
    ]["Player"].dropna().unique()
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

# ==================================================
# PLAYER ROWS
# ==================================================

p1 = filtered_df[
    filtered_df["Player"] == player1
].iloc[0]

p2 = filtered_df[
    filtered_df["Player"] == player2
].iloc[0]

# ==================================================
# COLOR FUNCTION
# ==================================================

def get_color(value):

    if value >= 90:
        return "#123B6E"

    elif value >= 75:
        return "#2E6DB4"

    elif value >= 60:
        return "#6FA8DC"

    elif value >= 40:
        return "#B7D7F0"

    elif value >= 25:
        return "#F4B6B6"

    else:
        return "#D94B4B"

# ==================================================
# LABEL FUNCTION
# ==================================================

def get_label(value):

    if value >= 90:
        return "ELITE"

    elif value >= 75:
        return "EXCELLENT"

    elif value >= 60:
        return "GOOD"

    elif value >= 40:
        return "AVERAGE"

    elif value >= 25:
        return "BELOW AVG"

    else:
        return "WEAK"

# ==================================================
# SKILL TILE
# ==================================================

def comparison_tile(title, value):

    if pd.isna(value):
        value = 0

    value = int(round(value))

    color = get_color(value)

    label = get_label(value)

    html = f"""
    <div style="
        background:{color};
        border-radius:8px;
        height:68px;
        padding:4px;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
        font-family:Arial;
        color:black;
        margin-bottom:4px;
    ">

        <div style="
            font-size:10px;
            font-weight:700;
            text-align:center;
        ">
            {title}
        </div>

        <div style="
            font-size:22px;
            font-weight:800;
            line-height:1;
            margin-top:2px;
        ">
            {value}
        </div>

        <div style="
            font-size:8px;
            font-weight:700;
            margin-top:2px;
            letter-spacing:1px;
        ">
            {label}
        </div>

    </div>
    """

    components.html(
        html,
        height=74
    )

# ==================================================
# TITLE
# ==================================================

st.title("🏒 Liiga Player Comparison")

# ==================================================
# PLAYER HEADERS
# ==================================================

h1, h2, h3 = st.columns([5,1,5])

with h1:

    logo1 = get_logo(p1["Team"])

    if logo1:

        st.image(
            logo1,
            width=80
        )

    st.markdown(f"### {player1}")

    st.markdown(
        f"{p1['Team']} | {p1['Position']}"
    )

with h2:

    st.markdown("## VS")

with h3:

    logo2 = get_logo(p2["Team"])

    if logo2:

        st.image(
            logo2,
            width=80
        )

    st.markdown(f"### {player2}")

    st.markdown(
        f"{p2['Team']} | {p2['Position']}"
    )

# ==================================================
# SKILL COMPARISON
# ==================================================

st.markdown("## Skill Comparison")

skills = [

    ("Shooting", "Shooting Score"),
    ("Playmaking", "Playmaking Score"),
    ("Transition", "Transition Score"),
    ("Puck Movement", "Puck Movement Score"),
    ("Defense", "Defense Score"),
    ("Impact", "Impact Score"),
    ("Overall", "Overall Percentile")

]

for title, stat in skills:

    c1, c2, c3 = st.columns([5,1,5])

    with c1:
        comparison_tile(title, p1.get(stat, 0))

    with c2:
        st.markdown("")

    with c3:
        comparison_tile(title, p2.get(stat, 0))
