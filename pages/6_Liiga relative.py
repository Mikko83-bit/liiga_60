# =========================================================
# LIIGA RELATIVE IMPACT
# FINAL CLEAN VERSION + LOGOS
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

st.title(" Liiga Relative Impact")

# ==================================================
# LOAD DATA
# ==================================================

@st.cache_data
def load_data():

    FILE = "Liiga 2025-2026_skaters_teams.xlsx"

    df = pd.read_excel(FILE)

    # ==================================================
    # CLEAN COLUMNS
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
    )

    # ==================================================
    # REQUIRED COLUMNS
    # ==================================================

    required_cols = [

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
        "Time_on_ice"

    ]

    for col in required_cols:

        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    # ==================================================
    # GAMES
    # ==================================================

    if "Games_played" in df.columns:

        df["Games"] = pd.to_numeric(
            df["Games_played"],
            errors="coerce"
        ).fillna(0)

    elif "Games" in df.columns:

        df["Games"] = pd.to_numeric(
            df["Games"],
            errors="coerce"
        ).fillna(0)

    else:

        df["Games"] = 0

    # ==================================================
    # CLEAN
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

    df["TOI"] = pd.to_numeric(
        df["Time_on_ice"],
        errors="coerce"
    ).fillna(0)

    # ==================================================
    # PER60 FUNCTION
    # ==================================================

    def per60(stat):

        return np.where(
            df["TOI"] > 0,
            df[stat] / (df["TOI"] / 60),
            0
        )

    # ==================================================
    # PER60 STATS
    # ==================================================

    df["Goals60"] = per60("Goals")
    df["Assists60"] = per60("Assists")
    df["xG60"] = per60("xG")

    df["Entries60"] = per60("Entries")
    df["Breakouts60"] = per60("Breakouts")

    df["Takeaways60"] = per60("Takeaways")
    df["PuckLosses60"] = per60("Puck_losses")

    # ==================================================
    # xGF / xGA PER60
    # ==================================================

    df["xGF60"] = np.where(
        df["TOI"] > 0,
        df["Team_xG_when_on_ice"] / (df["TOI"] / 60),
        0
    )

    df["xGA60"] = np.where(
        df["TOI"] > 0,
        df["Opponents_xG_when_on_ice"] / (df["TOI"] / 60),
        0
    )

    # ==================================================
    # TEAM TABLE
    # ==================================================

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

    # ==================================================
    # TEAM ENVIRONMENT
    # ==================================================

    team_df["GF_per_Game"] = (
        team_df["Goals_for"] / 60
    )

    team_df["Goal_Diff"] = (
        team_df["Goals_for"] -
        team_df["Goals_against"]
    )

    team_df["Points_perc"] = (
        team_df["Points"] / 120
    )

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

    # ==================================================
    # MERGE TEAM DATA
    # ==================================================

    df = df.merge(
        team_df,
        on="Team",
        how="left"
    )

    # ==================================================
    # TEAM AVERAGES
    # ==================================================

    team_avg_xGF = (
        df.groupby("Team")["xGF60"]
        .transform("mean")
    )

    team_avg_goals = (
        df.groupby("Team")["Goals60"]
        .transform("mean")
    )

    team_avg_netxg = (
        df.groupby("Team")["NetxG"]
        .transform("mean")
    )

    team_avg_takeaways = (
        df.groupby("Team")["Takeaways60"]
        .transform("mean")
    )

    team_avg_losses = (
        df.groupby("Team")["PuckLosses60"]
        .transform("mean")
    )

    # ==================================================
    # RELATIVE METRICS
    # ==================================================

    df["Relative_xGF"] = (
        df["xGF60"] -
        team_avg_xGF
    )

    df["Relative_Offence"] = (
        df["Goals60"] -
        team_avg_goals
    )

    df["Relative_NetxG"] = (
        df["NetxG"] -
        team_avg_netxg
    )

    relative_takeaways = (
        df["Takeaways60"] -
        team_avg_takeaways
    )

    relative_losses = (
        df["PuckLosses60"] -
        team_avg_losses
    )

    # ==================================================
    # DEFENSE MODEL
    # ==================================================

    df["Defense_Raw"] = (

        relative_takeaways * 0.35 +

        df["Relative_NetxG"] * 0.45 -

        relative_losses * 0.20

    )

    # ==================================================
    # IMPACT MODEL
    # ==================================================

    df["Relative_Impact_Raw"] = (

        df["Relative_xGF"] * 0.35 +

        df["Defense_Raw"] * 0.30 +

        df["Relative_NetxG"] * 0.20 +

        df["Relative_Offence"] * 0.15

    )

    # ==================================================
    # POSITION PERCENTILES
    # ==================================================

    metrics = [

        "Relative_xGF",
        "Defense_Raw",
        "Relative_Offence",
        "Relative_NetxG",
        "Relative_Impact_Raw"

    ]

    for metric in metrics:

        df[f"{metric}_Pct"] = (

            df.groupby("Position")[metric]
            .rank(pct=True) * 100

        )

    # ==================================================
    # ROUND
    # ==================================================

    numeric_cols = df.select_dtypes(
        include=np.number
    ).columns

    df[numeric_cols] = (
        df[numeric_cols]
        .round(2)
    )

    return df


# ==================================================
# LOAD DATA
# ==================================================

df = load_data()

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

filtered_df = df[
    (df["TOI"] >= min_toi) &
    (df["Games"] >= min_games)
]

# ==================================================
# POSITION
# ==================================================

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

# ==================================================
# TEAM
# ==================================================

teams = sorted(
    filtered_df["Team"]
    .dropna()
    .unique()
)

selected_team = st.sidebar.selectbox(
    "Team",
    teams
)

team_filtered = filtered_df[
    filtered_df["Team"] == selected_team
]

# ==================================================
# PLAYER
# ==================================================

players = sorted(
    team_filtered["Player"]
    .dropna()
    .unique()
)

selected_player = st.sidebar.selectbox(
    "Player",
    players
)

player = team_filtered[
    team_filtered["Player"] == selected_player
].iloc[0]

# ==================================================
# HEADER
# ==================================================

logo = get_logo(player["Team"])

col1, col2 = st.columns([1,5])

with col1:

    if logo:
        st.image(logo, width=120)

with col2:

    st.markdown(
        f"""
        ## {player['Player']}

        {player['Team']} | {player['Position']}
        """
    )

# ==================================================
# TEAM ENVIRONMENT
# ==================================================

env_score = player["Team_Environment"]

if env_score >= 75:
    env_label = "Strong Team"

elif env_score >= 45:
    env_label = "Average Team"

else:
    env_label = "Weak Team"

# ==================================================
# TOP ROW
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
        f"{player['Relative_Impact_Raw_Pct']:.0f}%"
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

m1, m2, m3, m4 = st.columns(4)

with m1:

    st.metric(
        "Relative xGF",
        f"{player['Relative_xGF']:.2f}"
    )

with m2:

    st.metric(
        "Defense Impact",
        f"{player['Defense_Raw']:.2f}"
    )

with m3:

    st.metric(
        "Relative NetxG",
        f"{player['Relative_NetxG']:.2f}"
    )

with m4:

    st.metric(
        "Relative Offence",
        f"{player['Relative_Offence']:.2f}"
    )

# ==================================================
# PERCENTILES
# ==================================================

st.markdown("## Relative Percentiles")

gauge_cols = st.columns(5)

gauges = [

    ("xGF", "Relative_xGF_Pct"),
    ("Defense", "Defense_Raw_Pct"),
    ("NetxG", "Relative_NetxG_Pct"),
    ("Offence", "Relative_Offence_Pct"),
    ("Impact", "Relative_Impact_Raw_Pct")

]

for col, (title, stat) in zip(gauge_cols, gauges):

    with col:

        value = player[stat]

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4F8BFF"},
                "bgcolor": "#111111"
            },
            title={"text": title}
        ))

        fig.update_layout(
            height=220,
            margin=dict(
                l=10,
                r=10,
                t=40,
                b=10
            ),
            paper_bgcolor="#0E1117",
            font=dict(color="white")
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# ==================================================
# LEADERBOARD
# ==================================================

st.markdown("## Relative Leaderboard")

leaderboard = filtered_df[[
    "Player",
    "Team",
    "Relative_Impact_Raw_Pct",
    "Relative_xGF_Pct",
    "Defense_Raw_Pct",
    "Relative_NetxG_Pct",
    "Relative_Offence_Pct"
]].sort_values(
    "Relative_Impact_Raw_Pct",
    ascending=False
)

st.dataframe(
    leaderboard,
    use_container_width=True,
    hide_index=True
)
