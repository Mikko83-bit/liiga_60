# =========================================================
# TRUE POINT SHARES MODEL
# TOI-BASED DEFENSIVE ALLOCATION
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Liiga Point Shares",
    page_icon="🏒",
    layout="wide"
)

st.title("🏒 Liiga Point Shares 2025-2026")

# =========================================================
# FILE
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# =========================================================
# CLEAN COLUMNS
# =========================================================

def clean_columns(df):

    df.columns = (

        df.columns

        .str.strip()

        .str.replace(" ", "_")
        .str.replace("/", "_")
        .str.replace("%", "perc")
        .str.replace("-", "_")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)

    )

    return df


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    # =====================================================
    # READ EXCEL
    # =====================================================

    players = pd.read_excel(
        FILE,
        sheet_name="Skaters"
    )

    teams = pd.read_excel(
        FILE,
        sheet_name="Teams"
    )

    # =====================================================
    # CLEAN
    # =====================================================

    players = clean_columns(players)
    teams = clean_columns(teams)

    # =====================================================
    # TEAM CLEAN
    # =====================================================

    players["Team"] = (
        players["Team"]
        .astype(str)
        .str.strip()
    )

    teams["Team"] = (
        teams["Team"]
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # NUMERIC PLAYER COLUMNS
    # =====================================================

    player_numeric = [

        "Goals",
        "Assists",
        "xG",
        "Time_on_ice",
        "Passes_to_the_slot",
        "Takeaways",
        "Puck_losses",
        "Puck_battles_won",
        "NetxG",
        "Penalties_drawn",
        "Penalties"

    ]

    for col in player_numeric:

        players[col] = pd.to_numeric(
            players[col],
            errors="coerce"
        ).fillna(0)

    # =====================================================
    # NUMERIC TEAM COLUMNS
    # =====================================================

    team_numeric = [

        "Games",
        "Goals_for",
        "Goals_agn"

    ]

    for col in team_numeric:

        teams[col] = pd.to_numeric(
            teams[col],
            errors="coerce"
        ).fillna(0)

    # =====================================================
    # LEAGUE BASELINES
    # =====================================================

    league_goals_per_game = (

        teams["Goals_for"].sum()

        /

        teams["Games"].sum()

    )

    # =====================================================
    # TEAM MGF / MGA
    # =====================================================

    teams["MGF"] = (

        teams["Goals_for"]

        -

        (
            (7 / 12)

            *

            teams["Games"]

            *

            league_goals_per_game
        )

    )

    teams["MGA"] = (

        (
            1 + (7 / 12)
        )

        *

        teams["Games"]

        *

        league_goals_per_game

        -

        teams["Goals_agn"]

    )

    # =====================================================
    # MERGE
    # =====================================================

    df = players.merge(

        teams[
            [
                "Team",
                "MGF",
                "MGA"
            ]
        ],

        on="Team",
        how="left"

    )

    # =====================================================
    # TOI
    # =====================================================

    df["TOI"] = pd.to_numeric(
        df["Time_on_ice"],
        errors="coerce"
    ).fillna(0)

    # =====================================================
    # TEAM TOI
    # =====================================================

    team_toi = (

        df.groupby("Team")["TOI"]
        .sum()
        .reset_index()

    )

    team_toi.columns = [
        "Team",
        "TeamTOI"
    ]

    df = df.merge(
        team_toi,
        on="Team",
        how="left"
    )

    # =====================================================
    # GOALS CREATED
    # =====================================================

    df["GoalsCreated"] = (

        df["Goals"]

        +

        (
            0.7
            *
            df["Assists"]
        )

        +

        (
            0.15
            *
            df["Passes_to_the_slot"]
        )

        +

        (
            0.10
            *
            df["xG"]
        )

    )

    # =====================================================
    # TEAM GOALS CREATED
    # =====================================================

    team_gc = (

        df.groupby("Team")["GoalsCreated"]
        .sum()
        .reset_index()

    )

    team_gc.columns = [
        "Team",
        "TeamGoalsCreated"
    ]

    df = df.merge(
        team_gc,
        on="Team",
        how="left"
    )

    # =====================================================
    # OFFENSIVE SHARE
    # =====================================================

    df["OffensiveShare"] = (

        df["GoalsCreated"]

        /

        df["TeamGoalsCreated"]

    )

    df["OffensiveShare"] = (
        df["OffensiveShare"]
        .replace([np.inf, -np.inf], 0)
        .fillna(0)
    )

    # =====================================================
    # OFFENSIVE POINT SHARES
    # =====================================================

    df["OPS"] = (

        df["OffensiveShare"]

        *

        df["MGF"]

    )

    # =====================================================
    # BASE DEFENSIVE SHARE (TOI BASED)
    # =====================================================

    df["TOIShare"] = (

        df["TOI"]

        /

        df["TeamTOI"]

    )

    df["TOIShare"] = (
        df["TOIShare"]
        .replace([np.inf, -np.inf], 0)
        .fillna(0)
    )

    # =====================================================
    # POSITION ADJUSTMENT
    # =====================================================

    df["PositionAdjustment"] = np.where(

        df["Position"] == "D",

        1.15,

        0.90

    )

    # =====================================================
    # BASE DPS
    # =====================================================

    df["BaseDPS"] = (

        df["TOIShare"]

        *

        df["MGA"]

        *

        df["PositionAdjustment"]

    )

    # =====================================================
    # DEFENSIVE MODIFIER
    # SMALL ADJUSTMENT ONLY
    # =====================================================

    df["DefensiveModifier"] = (

        1

        +

        (
            0.015
            *
            df["NetxG"]
        )

        +

        (
            0.002
            *
            df["Takeaways"]
        )

        -

        (
            0.002
            *
            df["Puck_losses"]
        )

        +

        (
            0.001
            *
            df["Puck_battles_won"]
        )

        +

        (
            0.01
            *
            (
                df["Penalties_drawn"]
                -
                df["Penalties"]
            )
        )

    )

    # =====================================================
    # CLIP MODIFIER
    # =====================================================

    df["DefensiveModifier"] = (
        df["DefensiveModifier"]
        .clip(0.75, 1.25)
    )

    # =====================================================
    # FINAL DPS
    # =====================================================

    df["DPS"] = (

        df["BaseDPS"]

        *

        df["DefensiveModifier"]

    )

    # =====================================================
    # TOI STABILIZATION
    # =====================================================

    K = 400

    df["TOI_Factor"] = (

        df["TOI"]

        /

        (
            df["TOI"] + K
        )

    )

    df["OPS"] = (
        df["OPS"]
        *
        df["TOI_Factor"]
    )

    df["DPS"] = (
        df["DPS"]
        *
        df["TOI_Factor"]
    )

    # =====================================================
    # FINAL POINT SHARES
    # =====================================================

    df["PointShares"] = (
        df["OPS"]
        +
        df["DPS"]
    )

    # =====================================================
    # PERCENTILE
    # =====================================================

    df["PS_percentile"] = (

        df["PointShares"]

        .rank(pct=True)

        * 100

    )

    # =====================================================
    # CLEAN
    # =====================================================

    df = df.replace(
        [np.inf, -np.inf],
        0
    )

    df = df.fillna(0)

    return df


# =========================================================
# LOAD
# =========================================================

df = load_data()

# =========================================================
# FILTERS
# =========================================================

c1, c2 = st.columns(2)

with c1:

    team_filter = st.selectbox(
        "Team",
        ["All"] +
        sorted(df["Team"].unique())
    )

with c2:

    position_filter = st.selectbox(
        "Position",
        ["All", "F", "D"]
    )

# =========================================================
# FILTER DATA
# =========================================================

filtered_df = df.copy()

if team_filter != "All":

    filtered_df = filtered_df[
        filtered_df["Team"] == team_filter
    ]

if position_filter != "All":

    filtered_df = filtered_df[
        filtered_df["Position"] == position_filter
    ]

# =========================================================
# TABLE
# =========================================================

st.subheader("Top Point Shares")

table = (

    filtered_df[[
        "Player",
        "Team",
        "Position",
        "OPS",
        "DPS",
        "PointShares",
        "PS_percentile"
    ]]

    .sort_values(
        "PointShares",
        ascending=False
    )

)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# PLAYER CARD
# =========================================================

st.divider()

st.header("Player Card")

selected_player = st.selectbox(
    "Choose Player",
    sorted(df["Player"].unique())
)

player_df = df[
    df["Player"] == selected_player
]

player = player_df.iloc[0]

# =========================================================
# PLAYER HEADER
# =========================================================

st.subheader(
    f"{player['Player']} | {player['Team']} | {player['Position']}"
)

# =========================================================
# METRICS
# =========================================================

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "OPS",
        round(player["OPS"], 2)
    )

with c2:

    st.metric(
        "DPS",
        round(player["DPS"], 2)
    )

with c3:

    st.metric(
        "Point Shares",
        round(player["PointShares"], 2)
    )

# =========================================================
# PLAYER DETAILS
# =========================================================

stats = pd.DataFrame({

    "Metric": [

        "Goals",
        "Assists",
        "xG",
        "Goals Created",
        "NetxG",
        "Takeaways",
        "Puck Losses",
        "TOI"

    ],

    "Value": [

        round(player["Goals"], 1),
        round(player["Assists"], 1),
        round(player["xG"], 1),
        round(player["GoalsCreated"], 1),
        round(player["NetxG"], 1),
        round(player["Takeaways"], 1),
        round(player["Puck_losses"], 1),
        round(player["TOI"], 1)

    ]

})

st.dataframe(
    stats,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# DISTRIBUTION
# =========================================================

st.divider()

st.header("Point Share Distribution")

fig = px.histogram(
    df,
    x="PointShares",
    nbins=40
)

st.plotly_chart(
    fig,
    use_container_width=True
)
