# =========================================================
# LIIGA WINSHARE MODEL 2025-2026
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import zscore
import plotly.express as px

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Liiga Winshares",
    page_icon="🏒",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("🏒 Liiga Winshares 2025-2026")

# =========================================================
# FILE
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# =========================================================
# HELPERS
# =========================================================

def safe_z(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    if len(series.unique()) <= 1:
        return np.zeros(len(series))

    return zscore(series)


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
    # CLEAN COLUMNS
    # =====================================================

    players = clean_columns(players)
    teams = clean_columns(teams)

    # =====================================================
    # CLEAN TEAM NAMES
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
    # TEAM STATS
    # =====================================================

    teams["GPG"] = (

        pd.to_numeric(
            teams["Goals_for"],
            errors="coerce"
        ).fillna(0)

        /

        pd.to_numeric(
            teams["Games_played"],
            errors="coerce"
        ).fillna(1)

    )

    teams["GAPG"] = (

        pd.to_numeric(
            teams["Goals_agn"],
            errors="coerce"
        ).fillna(0)

        /

        pd.to_numeric(
            teams["Games_played"],
            errors="coerce"
        ).fillna(1)

    )

    # =====================================================
    # MERGE
    # =====================================================

    df = players.merge(
        teams,
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

    df["TOI"] = df["TOI"].replace(0, np.nan)

    # =====================================================
    # NUMERIC COLUMNS
    # =====================================================

    numeric_cols = [

        "Goals",
        "Assists",
        "xG",
        "Passes_to_the_slot",
        "Takeaways",
        "Puck_losses",
        "Puck_battles_won",
        "Entries_via_stickhandling",
        "Breakouts_via_stickhandling",
        "CORSI_for",
        "NetxG"

    ]

    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    # =====================================================
    # PER 60 STATS
    # =====================================================

    df["Goals60"] = (
        df["Goals"] / df["TOI"]
    ) * 60

    df["Assists60"] = (
        df["Assists"] / df["TOI"]
    ) * 60

    df["xG60"] = (
        df["xG"] / df["TOI"]
    ) * 60

    df["SlotPass60"] = (
        df["Passes_to_the_slot"] / df["TOI"]
    ) * 60

    df["Takeaways60"] = (
        df["Takeaways"] / df["TOI"]
    ) * 60

    df["PuckLoss60"] = (
        df["Puck_losses"] / df["TOI"]
    ) * 60

    df["Battles60"] = (
        df["Puck_battles_won"] / df["TOI"]
    ) * 60

    df["Entries60"] = (
        df["Entries_via_stickhandling"] / df["TOI"]
    ) * 60

    df["Breakouts60"] = (
        df["Breakouts_via_stickhandling"] / df["TOI"]
    ) * 60

    # =====================================================
    # NET XG
    # =====================================================

    df["NetxG"] = pd.to_numeric(
        df["NetxG"],
        errors="coerce"
    ).fillna(0)

    # =====================================================
    # CLEAN
    # =====================================================

    df = df.replace(
        [np.inf, -np.inf],
        0
    )

    df = df.fillna(0)

    # =====================================================
    # POSITION ADJUSTED Z-SCORES
    # =====================================================

    metrics = [

        "Goals60",
        "Assists60",
        "xG60",
        "SlotPass60",

        "Takeaways60",
        "PuckLoss60",
        "Battles60",
        "Entries60",
        "Breakouts60",
        "NetxG",
        "CORSI_for"

    ]

    for metric in metrics:

        df[f"{metric}_z"] = 0.0

    for position in ["F", "D"]:

        mask = (
            df["Position"] == position
        )

        pos_df = df[mask]

        for metric in metrics:

            df.loc[
                mask,
                f"{metric}_z"
            ] = safe_z(
                pos_df[metric]
            )

    # =====================================================
    # TEAM OFFENSE STRENGTH
    # =====================================================

    league_gpg = df["GPG"].mean()

    df["Team_Off_Strength"] = (
        df["GPG"] / league_gpg
    )

    # =====================================================
    # RAW OWS
    # =====================================================

    df["Raw_OWS"] = (

        0.30 * df["Goals60_z"] +

        0.35 * df["Assists60_z"] +

        0.20 * df["xG60_z"] +

        0.15 * df["SlotPass60_z"]

    )

    # =====================================================
    # RAW DWS
    # =====================================================

    df["Raw_DWS"] = (

        0.20 * df["Takeaways60_z"] -

        0.20 * df["PuckLoss60_z"] +

        0.15 * df["Battles60_z"] +

        0.15 * df["Breakouts60_z"] +

        0.15 * df["NetxG_z"] +

        0.15 * df["CORSI_for_z"]

    )

    # =====================================================
    # TEAM ADJUSTMENT
    # =====================================================

    df["OWS"] = (

        df["Raw_OWS"]

        -

        (
            (
                df["Team_Off_Strength"] - 1
            ) * 0.35
        )

    )

    # =====================================================
    # DWS
    # =====================================================

    df["DWS"] = df["Raw_DWS"]

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

    df["OWS"] = (
        df["OWS"] *
        df["TOI_Factor"]
    )

    df["DWS"] = (
        df["DWS"] *
        df["TOI_Factor"]
    )

    # =====================================================
    # FINAL WS
    # =====================================================

    df["WS"] = (
        df["OWS"] +
        df["DWS"]
    )

    # =====================================================
    # PERCENTILES
    # =====================================================

    df["WS_percentile"] = (
        df["WS"]
        .rank(pct=True) * 100
    )

    return df


# =========================================================
# LOAD DATA
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
# WINSHARE TABLE
# =========================================================

st.subheader("Top Win Shares")

table = (

    filtered_df[[
        "Player",
        "Team",
        "Position",
        "OWS",
        "DWS",
        "WS",
        "WS_percentile"
    ]]

    .sort_values(
        "WS",
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
# PLAYER INFO
# =========================================================

st.subheader(
    f"{player['Player']} | {player['Team']} | {player['Position']}"
)

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "OWS",
        round(player["OWS"], 2)
    )

with c2:

    st.metric(
        "DWS",
        round(player["DWS"], 2)
    )

with c3:

    st.metric(
        "WS",
        round(player["WS"], 2)
    )

# =========================================================
# PLAYER STATS TABLE
# =========================================================

stats_table = pd.DataFrame({

    "Statistic": [

        "Goals/60",
        "Assists/60",
        "xG/60",
        "Takeaways/60",
        "Puck Losses/60",
        "Entries/60",
        "Breakouts/60"

    ],

    "Value": [

        round(player["Goals60"], 2),
        round(player["Assists60"], 2),
        round(player["xG60"], 2),
        round(player["Takeaways60"], 2),
        round(player["PuckLoss60"], 2),
        round(player["Entries60"], 2),
        round(player["Breakouts60"], 2)

    ]

})

st.dataframe(
    stats_table,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# WS DISTRIBUTION
# =========================================================

st.divider()

st.header("WS Distribution")

fig = px.histogram(
    df,
    x="WS",
    nbins=40
)

st.plotly_chart(
    fig,
    use_container_width=True
)
