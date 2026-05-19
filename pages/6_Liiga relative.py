# =========================================================
# LIIGA RELATIVE IMPACT
# pages/6_Liiga_Relative.py
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# ==================================================
# PAGE CONFIG
# ==================================================

st.set_page_config(
    page_title="Liiga Relative Impact",
    layout="wide"
)

# ==================================================
# TITLE
# ==================================================

st.title("🏒 Liiga Relative Impact")

# ==================================================
# LOAD DATA
# ==================================================

@st.cache_data
def load_data():

    FILE = "Liiga 2025-2026_skaters_teams.xlsx"

    df = pd.read_excel(FILE)

    # ==========================================
    # CLEAN COLUMNS
    # ==========================================

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
    )

    # ==========================================
    # NUMERIC
    # ==========================================

    numeric_cols = [

        "Goals",
        "Assists",
        "xG",
        "Shots_on_goal",
        "Entries",
        "Breakouts",
        "Takeaways",
        "Puck_losses",
        "NetxG",
        "Team_xG_when_on_ice",
        "Opponents_xG_when_on_ice",
        "Time_on_ice",
        "Games_played"

    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

        else:

            df[col] = 0

    # ==========================================
    # TOI
    # ==========================================

    df["TOI"] = df["Time_on_ice"]

    # ==========================================
    # PER60
    # ==========================================

    def per60(stat):

        return np.where(
            df["TOI"] > 0,
            (df[stat] / df["TOI"]) * 60,
            0
        )

    df["Goals60"] = per60("Goals")
    df["Assists60"] = per60("Assists")
    df["xG60"] = per60("xG")
    df["Shots60"] = per60("Shots_on_goal")
    df["Entries60"] = per60("Entries")
    df["Breakouts60"] = per60("Breakouts")
    df["Takeaways60"] = per60("Takeaways")

    # ==========================================
    # ON-ICE xG
    # ==========================================

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

    # ==========================================
    # TEAM TABLE
    # ==========================================

    team_data = {

        "Team": [
            "TAPPARA","KOOKOO","SAIPA","ILVES",
            "LUKKO","JYP","KALPA","ASSAT",
            "ESPOO","HIFK","PELICANS","HPK",
            "TPS","KARPAT","JUKURIT","SPORT"
        ],

        "Points": [
            117,115,112,107,
            106,106,104,94,
            90,88,85,75,
            71,66,64,40
        ],

        "Goals_for": [
            226,217,204,186,
            185,202,185,170,
            157,149,137,144,
            141,175,131,108
        ],

        "Goals_against": [
            149,155,162,152,
            157,180,179,165,
            155,183,156,167,
            177,197,171,212
        ]

    }

    team_df = pd.DataFrame(team_data)

    # ==========================================
    # TEAM METRICS
    # ==========================================

    team_df["GF_per_Game"] = (
        team_df["Goals_for"] / 60
    )

    team_df["GA_per_Game"] = (
        team_df["Goals_against"] / 60
    )

    team_df["Goal_Diff"] = (
        team_df["Goals_for"] -
        team_df["Goals_against"]
    )

    team_df["Points_perc"] = (
        team_df["Points"] / 120
    )

    # ==========================================
    # TEAM ENVIRONMENT SCORE
    # ==========================================

    team_df["Team_Environment"] = (

        team_df["Points_perc"] * 0.4 +

        (
            team_df["GF_per_Game"] /
            team_df["GF_per_Game"].max()
        ) * 0.3 +

        (
            (
                team_df["Goal_Diff"] -
                team_df["Goal_Diff"].min()
            ) /

            (
                team_df["Goal_Diff"].max() -
                team_df["Goal_Diff"].min()
            )
        ) * 0.3

    ) * 100

    # ==========================================
    # MERGE TEAM DATA
    # ==========================================

    df = df.merge(
        team_df,
        on="Team",
        how="left"
    )

    # ==========================================
    # RELATIVE METRICS
    # ==========================================

    team_avg_xGF = (
        df.groupby("Team")["xGF60"]
        .transform("mean")
    )

    team_avg_xGA = (
        df.groupby("Team")["xGA60"]
        .transform("mean")
    )

    team_avg_netxg = (
        df.groupby("Team")["NetxG"]
        .transform("mean")
    )

    team_avg_goals = (
        df.groupby("Team")["Goals60"]
        .transform("mean")
    )

    # ==========================================
    # RELATIVE IMPACT
    # ==========================================

    df["Relative_xGF"] = (
        df["xGF60"] -
        team_avg_xGF
    )

    df["Relative_xGA"] = (
        team_avg_xGA -
        df["xGA60"]
    )

    df["Relative_NetxG"] = (
        df["NetxG"] -
        team_avg_netxg
    )

    df["Relative_Offence"] = (
        df["Goals60"] -
        team_avg_goals
    )

    # ==========================================
    # IMPACT SCORE
    # ==========================================

    df["Relative_Impact_Raw"] = (

        df["Relative_xGF"] * 0.35 +

        df["Relative_xGA"] * 0.25 +

        df["Relative_NetxG"] * 0.25 +

        df["Relative_Offence"] * 0.15

    )

    # ==========================================
    # POSITION PERCENTILES
    # ==========================================

    metrics = [

        "Relative_xGF",
        "Relative_xGA",
        "Relative_NetxG",
        "Relative_Offence",
        "Relative_Impact_Raw"

    ]

    for metric in metrics:

        percentile_col = f"{metric}_Pct"

        df[percentile_col] = (

            df.groupby("Position")[metric]
            .rank(pct=True) * 100

        )

    # ==========================================
    # ROUND
    # ==========================================

    numeric = df.select_dtypes(include=np.number).columns

    df[numeric] = df[numeric].round(2)

    return df


df = load_data()

# ==================================================
# SIDEBAR
# ==================================================

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

# ==========================================
# FILTERS
# ==========================================

filtered_df = df[
    (df["TOI"] >= min_toi)
]

if "Games_played" in filtered_df.columns:

    filtered_df = filtered_df[
        filtered_df["Games_played"] >= min_games
    ]

# ==========================================
# POSITION
# ==========================================

positions = sorted(
    filtered_df["Position"]
    .dropna()
    .unique()
)

selected_position = st.sidebar.selectbox(
    "Position",
    positions
)

filtered_df = filtered_df[
    filtered_df["Position"] == selected_position
]

# ==========================================
# TEAM
# ==========================================

teams = sorted(
    filtered_df["Team"]
    .dropna()
    .unique()
)

selected_team = st.sidebar.selectbox(
    "Team",
    teams
)

team_df = filtered_df[
    filtered_df["Team"] == selected_team
]

# ==========================================
# PLAYER
# ==========================================

players = sorted(
    team_df["Player"]
    .dropna()
    .unique()
)

selected_player = st.sidebar.selectbox(
    "Player",
    players
)

player = team_df[
    team_df["Player"] == selected_player
].iloc[0]

# ==================================================
# HEADER
# ==================================================

st.markdown(
    f"## {player['Player']} | {player['Team']} | {player['Position']}"
)

# ==================================================
# TEAM ENVIRONMENT
# ==================================================

env_score = player["Team_Environment"]

env_label = "Strong Team"

if env_score < 45:
    env_label = "Weak Team"

elif env_score < 65:
    env_label = "Average Team"

# ==================================================
# TOP METRICS
# ==================================================

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "Team Environment",
        f"{env_score:.1f}"
    )

with c2:

    st.metric(
        "Relative Impact",
        f"{player['Relative_Impact_Raw_Pct']:.0f} %"
    )

with c3:

    st.metric(
        "Environment Label",
        env_label
    )

# ==================================================
# RELATIVE METRICS
# ==================================================

st.markdown("---")

metric_cols = st.columns(4)

metrics = [

    ("Relative xGF", "Relative_xGF"),
    ("Relative xGA", "Relative_xGA"),
    ("Relative NetxG", "Relative_NetxG"),
    ("Relative Offence", "Relative_Offence")

]

for col, (label, stat) in zip(metric_cols, metrics):

    with col:

        st.metric(
            label,
            f"{player[stat]:.2f}"
        )

# ==================================================
# PERCENTILES
# ==================================================

st.markdown("## Relative Percentiles")

percentile_cols = st.columns(5)

pct_metrics = [

    ("xGF", "Relative_xGF_Pct"),
    ("xGA", "Relative_xGA_Pct"),
    ("NetxG", "Relative_NetxG_Pct"),
    ("Offence", "Relative_Offence_Pct"),
    ("Impact", "Relative_Impact_Raw_Pct")

]

for col, (label, stat) in zip(percentile_cols, pct_metrics):

    with col:

        value = player[stat]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                "axis": {"range": [0,100]},
                "bar": {"color": "#4F8BFF"},
                "bgcolor": "#111111"
            },
            title={"text": label}
        ))

        fig.update_layout(
            height=220,
            margin=dict(l=10,r=10,t=40,b=10),
            paper_bgcolor="#0E1117",
            font=dict(color="white")
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ==================================================
# TABLE
# ==================================================

st.markdown("## Relative Leaderboard")

leaderboard = filtered_df[[
    "Player",
    "Team",
    "Relative_Impact_Raw_Pct",
    "Relative_xGF_Pct",
    "Relative_xGA_Pct",
    "Relative_NetxG_Pct"
]].sort_values(
    "Relative_Impact_Raw_Pct",
    ascending=False
)

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True
)
