import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import zscore

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="SDHL Player Profiles",
    page_icon="🏒",
    layout="wide"
)

# ---------------------------------------------------
# FILE (Päivitetty uusi tiedostonimi)
# ---------------------------------------------------
FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data
def load_data():
    # ---------------------------------------------------
    # READ EXCEL
    # ---------------------------------------------------
    players = pd.read_excel(FILE, sheet_name="Player")
    teams = pd.read_excel(FILE, sheet_name="Teams")

    # ---------------------------------------------------
    # CLEAN COLUMN NAMES
    # ---------------------------------------------------
    players.columns = (
        players.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_per_")
        .str.replace("%", "perc")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
    )

    teams.columns = (
        teams.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_per_")
        .str.replace("%", "perc")
    )

    # REMOVE DOUBLE UNDERSCORES
    players.columns = players.columns.str.replace("__", "_")
    players.columns = players.columns.str.replace("__", "_")

    teams.columns = teams.columns.str.replace("__", "_")
    teams.columns = teams.columns.str.replace("__", "_")

    # ---------------------------------------------------
    # TEAM STATS
    # ---------------------------------------------------
    teams["GPG"] = (
        teams["Goal_for"] / teams["GP"]
    )

    teams["GAPG"] = (
        teams["Goal_agn"] / teams["GP"]
    )

    # ---------------------------------------------------
    # MERGE
    # ---------------------------------------------------
    df = players.merge(teams, on="Team")

    # ---------------------------------------------------
    # FIX PLAYER POSITIONS
    # ---------------------------------------------------
    df.loc[
        df["Player"] == "Elisa Holopainen",
        "Position"
    ] = "F"

    # ---------------------------------------------------
    # RENAME IMPORTANT COLUMNS
    # ---------------------------------------------------
    rename_dict = {
        # OFFENSE
        "Goals_per_60": "Goals60",
        "Assists_per_60": "Assists60",
        "xG_per_60": "xG60",

        # DEFENSE
        "Takeaways_per_60": "Takeaways60",
        "Puck_losses_per_60": "PuckLosses60",
        "Net_penalties_per_60": "NetPenalties60",

        # OTHER
        "Passes_to_the_slot": "SlotPasses",
        "Puck_battles_won": "PuckBattlesWon",
        "Net_xG": "NetxG"
    }

    df = df.rename(columns=rename_dict)

    # ---------------------------------------------------
    # FILL NaN VALUES
    # ---------------------------------------------------
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # ---------------------------------------------------
    # METRICS
    # ---------------------------------------------------
    metrics = [
        # OFFENSE
        "Goals60",
        "Assists60",
        "xG60",
        "Scoring_chances",
        "SlotPasses",

        # DEFENSE
        "NetxG",
        "Takeaways60",
        "PuckLosses60",
        "NetPenalties60",
        "PuckBattlesWon"
    ]

    # ---------------------------------------------------
    # CREATE EMPTY Z-SCORE COLUMNS
    # ---------------------------------------------------
    for metric in metrics:
        df[f"{metric}_z"] = 0.0

    # ---------------------------------------------------
    # POSITION-ADJUSTED Z-SCORES
    # ---------------------------------------------------
    for position in ["F", "D"]:
        pos_mask = df["Position"] == position

        for metric in metrics:
            if metric in df.columns:
                values = df.loc[pos_mask, metric]
                z_values = zscore(values)
                z_values = np.nan_to_num(z_values)
                df.loc[
                    pos_mask,
                    f"{metric}_z"
                ] = z_values.astype(float)

    # ---------------------------------------------------
    # LEAGUE AVERAGES
    # ---------------------------------------------------
    league_gpg = teams["GPG"].mean()
    league_gapg = teams["GAPG"].mean()

    # ---------------------------------------------------
    # TEAM ADJUSTMENTS
    # ---------------------------------------------------
    df["Team_Off_Strength"] = (
        df["GPG"] / league_gpg
    )

    df["Team_Def_Strength"] = (
        league_gapg / df["GAPG"]
    )

    # ---------------------------------------------------
    # RAW OFFENSIVE WIN SHARES
    # ---------------------------------------------------
    df["Raw_OWS"] = (
        0.30 * df["Goals60_z"] +
        0.35 * df["Assists60_z"] +
        0.20 * df["xG60_z"] +
        0.15 * df["SlotPasses_z"]
    )

    # ---------------------------------------------------
    # RAW DEFENSIVE WIN SHARES
    # ---------------------------------------------------
    df["Raw_DWS"] = (
        0.40 * df["NetxG_z"] +
        0.20 * df["Takeaways60_z"] -
        0.20 * df["PuckLosses60_z"] +
        0.10 * df["NetPenalties60_z"] +
        0.10 * df["PuckBattlesWon_z"]
    )

    # ---------------------------------------------------
    # TEAM-ADJUSTED WIN SHARES
    # ---------------------------------------------------
    df["OWS"] = (
        df["Raw_OWS"] -
        ((df["Team_Off_Strength"] - 1) * 0.50)
    )

    df["DWS"] = (
        df["Raw_DWS"] -
        ((df["Team_Def_Strength"] - 1) * 0.50)
    )

    # ---------------------------------------------------
    # TOI STABILIZATION
    # ---------------------------------------------------
    K = 400

    df["TOI_Factor"] = (
        df["Time_on_ice"] /
        (df["Time_on_ice"] + K)
    )

    # APPLY STABILIZATION
    df["OWS"] = (
        df["OWS"] * df["TOI_Factor"]
    )

    df["DWS"] = (
        df["DWS"] * df["TOI_Factor"]
    )

    # ---------------------------------------------------
    # TOTAL WIN SHARES
    # ---------------------------------------------------
    df["WS"] = df["OWS"] + df["DWS"]

    # ---------------------------------------------------
    # PERCENTILES
    # ---------------------------------------------------
    df["OWS_percentile"] = (
        df["OWS"]
        .rank(pct=True) * 100
    )

    df["DWS_percentile"] = (
        df["DWS"]
        .rank(pct=True) * 100
    )

    df["WS_percentile"] = (
        df["WS"]
        .rank(pct=True) * 100
    )

    # ---------------------------------------------------
    # RANKINGS
    # ---------------------------------------------------
    df["OWS_rank"] = (
        df["OWS"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    df["DWS_rank"] = (
        df["DWS"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    df["WS_rank"] = (
        df["WS"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    return df

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
df = load_data()

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------
st.title("🏒 SDHL Player Profiles")
st.markdown("""
This dashboard includes:
• Position-adjusted Win Shares
• Team-adjusted Win Shares
• TOI stabilization
• Offensive Win Shares (OWS)
• Defensive Win Shares (DWS)
• Overall Win Shares (WS)
• League percentiles
• League rankings
""")

# ---------------------------------------------------
# FILTERS
# ---------------------------------------------------
filter_col1, filter_col2, filter_col3 = st.columns(3)

# TEAM FILTER
with filter_col1:
    team_filter = st.selectbox(
        "Select Team",
        ["All"] + sorted(df["Team"].unique().tolist())
    )

# POSITION FILTER
with filter_col2:
    position_filter = st.selectbox(
        "Select Position",
        ["All", "F", "D"]
    )

# MINIMUM GAMES FILTER
with filter_col3:
    min_games = st.slider(
        "Minimum Games Played",
        1,
        int(df["Games_played"].max()),
        10
    )

# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------
filtered_df = df.copy()
if team_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Team"] == team_filter
    ]
if position_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Position"] == position_filter
    ]
filtered_df = filtered_df[
    filtered_df["Games_played"] >= min_games
]

# ---------------------------------------------------
# PLAYER SELECTOR
# ---------------------------------------------------
player = st.selectbox(
    "Select Player",
    sorted(filtered_df["Player"].unique())
)

# ---------------------------------------------------
# PLAYER DATA
# ---------------------------------------------------
player_df = filtered_df[
    filtered_df["Player"] == player
].iloc[0]

# ---------------------------------------------------
# PLAYER HEADER
# ---------------------------------------------------
st.subheader(
    f"{player_df['Player']} | "
    f"{player_df['Team']} | "
    f"{player_df['Position']}"
)

# ---------------------------------------------------
# MAIN METRICS
# ---------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "OWS",
        f"{round(player_df['OWS'], 2)} "
        f"(#{player_df['OWS_rank']})"
    )
with col2:
    st.metric(
        "DWS",
        f"{round(player_df['DWS'], 2)} "
        f"(#{player_df['DWS_rank']})"
    )
with col3:
    st.metric(
        "WS",
        f"{round(player_df['WS'], 2)} "
        f"(#{player_df['WS_rank']})"
    )

# ---------------------------------------------------
# PERCENTILES
# ---------------------------------------------------
st.subheader("League Percentiles")
p1, p2, p3 = st.columns(3)
with p1:
    st.metric(
        "OWS Percentile",
        f"{round(player_df['OWS_percentile'])}%"
    )
with p2:
    st.metric(
        "DWS Percentile",
        f"{round(player_df['DWS_percentile'])}%"
    )
with p3:
    st.metric(
        "WS Percentile",
        f"{round(player_df['WS_percentile'])}%"
    )

# ---------------------------------------------------
# PLAYER INFORMATION
# ---------------------------------------------------
st.subheader("Player Information")
info1, info2, info3, info4 = st.columns(4)
with info1:
    st.write(
        f"**Games Played:** "
        f"{player_df['Games_played']}"
    )
with info2:
    st.write(
        f"**Time on Ice:** "
        f"{round(player_df['Time_on_ice'], 1)}"
    )
with info3:
    st.write(
        f"**Points:** "
        f"{player_df['Points']}"
    )
with info4:
    st.write(
        f"**Net xG:** "
        f"{round(player_df['NetxG'], 2)}"
    )

# ---------------------------------------------------
# ADDITIONAL STATISTICS
# ---------------------------------------------------
st.subheader("Additional Statistics")
stats_df = pd.DataFrame({
    "Statistic": [
        "Goals/60",
        "Assists/60",
        "xG/60",
        "Takeaways/60",
        "Puck Losses/60",
        "Net Penalties/60",
        "Puck Battles Won",
        "Slot Passes"
    ],
    "Value": [
        round(player_df["Goals60"], 2),
        round(player_df["Assists60"], 2),
        round(player_df["xG60"], 2),
        round(player_df["Takeaways60"], 2),
        round(player_df["PuckLosses60"], 2),
        round(player_df["NetPenalties60"], 2),
        round(player_df["PuckBattlesWon"], 2),
        round(player_df["SlotPasses"], 2)
    ]
})
st.dataframe(
    stats_df,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------
# TOP 10 WIN SHARES
# ---------------------------------------------------
st.subheader("Top 10 Win Shares")
top_ws = (
    filtered_df[[
        "Player",
        "Team",
        "Position",
        "OWS",
        "DWS",
        "WS"
    ]]
    .sort_values("WS", ascending=False)
    .head(10)
)
st.dataframe(
    top_ws,
    use_container_width=True,
    hide_index=True
)
