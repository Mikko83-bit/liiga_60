import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import zscore

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Liiga Player Profiles",
    page_icon="🏒",
    layout="wide"
)

# ---------------------------------------------------
# FILE
# ---------------------------------------------------
FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data
def load_data():
    # READ EXCEL - Luetaan ensimmäinen (pelaajat) ja toinen (joukkueet) välilehti indekseillä
    players = pd.read_excel(FILE, sheet_name=0)
    teams = pd.read_excel(FILE, sheet_name=1)

    # CLEAN COLUMN NAMES
    players.columns = (
        players.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_per_")
        .str.replace("%", "perc")
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("-", "") # Poistetaan viivat, esim. Plus/minus -> Plus_per_minus
    )

    teams.columns = (
        teams.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("/", "_per_")
        .str.replace("%", "perc")
        .str.replace("-", "")
    )

    # REMOVE DOUBLE UNDERSCORES
    players.columns = players.columns.str.replace("__", "_")
    teams.columns = teams.columns.str.replace("__", "_")

    # ---------------------------------------------------
    # TEAM STATS (Varmista, että nämä sarakkeet löytyvät Teams-välilehdeltä)
    # ---------------------------------------------------
    # Jos Teams-välilehden sarakkeet ovat suomeksi, muuta nämä esim. "Tehdyt_maalit" jne.
    try:
        teams["GPG"] = teams["Goal_for"] / teams["GP"]
        teams["GAPG"] = teams["Goal_agn"] / teams["GP"]
    except KeyError:
        # Varamekanismi, jos sarakkeet ovat suomeksi Teams-taulukossa
        teams["GPG"] = teams["TM"] / teams["O"] if "TM" in teams.columns else 1.0
        teams["GAPG"] = teams[" PM"] / teams["O"] if "PM" in teams.columns else 1.0

    # ---------------------------------------------------
    # MERGE
    # ---------------------------------------------------
    df = players.merge(teams, on="Team")

    # ---------------------------------------------------
    # RENAME IMPORTANT COLUMNS (Mätsätty image_56c8cd.png mukaan)
    # ---------------------------------------------------
    rename_dict = {
        # OFFENSE
        "Goals": "Goals60",            # Käytetään sellaisenaan tai /60 jos data on suhteutettu
        "Assists": "Assists60",
        "xG": "xG60",
        "Scoring_chances_total": "Scoring_chances", # Kuvassa "Scoring chances - total" -> siivottuna "Scoring_chances__total" tai vast.
        "Passes_to_the_slot": "SlotPasses",

        # DEFENSE
        "Net_xG": "NetxG",
        "Takeaways": "Takeaways60",
        "Puck_losses": "PuckLosses60",
        "Net_penalties_per_60": "NetPenalties60", # Jos saraketta ei löydy, luodaan tyhjä alempana
        "Puck_battles_won": "PuckBattlesWon"
    }
    
    # Tehdään varalta manuaalinen mäppäys siivottujen nimien perusteella
    df = df.rename(columns=rename_dict)

    # Varmistetaan, että kaikki tarvittavat sarakkeet ovat olemassa (jos kuvasta puuttui jokin)
    required_cols = {
        "Goals60": "Goals", "Assists60": "Assists", "xG60": "xG", 
        "SlotPasses": "Passes_to_the_slot", "NetxG": "Net_xG", 
        "Takeaways60": "Takeaways", "PuckLosses60": "Puck_losses", 
        "PuckBattlesWon": "Puck_battles_won", "NetPenalties60": "Goals", # fallbackiksi "Goals"
        "Scoring_chances": "Goals" # fallback
    }
    
    for clean_name, fallback in required_cols.items():
        if clean_name not in df.columns:
            if fallback in df.columns:
                df[clean_name] = df[fallback]
            elif fallback.replace("_", "") in df.columns:
                df[clean_name] = df[fallback.replace("_", "")]
            else:
                df[clean_name] = 0.0

    # ---------------------------------------------------
    # FILL NaN VALUES
    # ---------------------------------------------------
    numeric_cols = df.select_dtypes(include=np.number).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # ---------------------------------------------------
    # METRICS FOR Z-SCORE
    # ---------------------------------------------------
    metrics = [
        "Goals60", "Assists60", "xG60", "Scoring_chances", "SlotPasses",
        "NetxG", "Takeaways60", "PuckLosses60", "NetPenalties60", "PuckBattlesWon"
    ]

    for metric in metrics:
        df[f"{metric}_z"] = 0.0

    # POSITION-ADJUSTED Z-SCORES
    for position in df["Position"].unique():
        pos_mask = df["Position"] == position
        for metric in metrics:
            if metric in df.columns:
                values = df.loc[pos_mask, metric]
                if len(values) > 1 and values.std() > 0:
                    z_values = zscore(values)
                    df.loc[pos_mask, f"{metric}_z"] = np.nan_to_num(z_values).astype(float)

    # LEAGUE AVERAGES & STRENGTHS
    league_gpg = teams["GPG"].mean() if "GPG" in teams.columns else 1.0
    league_gapg = teams["GAPG"].mean() if "GAPG" in teams.columns else 1.0
    df["Team_Off_Strength"] = df["GPG"] / league_gpg if league_gpg > 0 else 1.0
    df["Team_Def_Strength"] = league_gapg / df["GAPG"] if "GAPG" in df.columns else 1.0

    # WIN SHARES FORMULAS
    df["Raw_OWS"] = (0.30 * df["Goals60_z"] + 0.35 * df["Assists60_z"] + 0.20 * df["xG60_z"] + 0.15 * df["SlotPasses_z"])
    df["Raw_DWS"] = (0.40 * df["NetxG_z"] + 0.20 * df["Takeaways60_z"] - 0.20 * df["PuckLosses60_z"] + 0.10 * df["PuckBattlesWon_z"])

    df["OWS"] = df["Raw_OWS"] - ((df["Team_Off_Strength"] - 1) * 0.50)
    df["DWS"] = df["Raw_DWS"] - ((df["Team_Def_Strength"] - 1) * 0.50)

    # TOI STABILIZATION (Kuvassa sarake on "Time on ice" -> siivottuna "Time_on_ice")
    toi_col = "Time_on_ice" if "Time_on_ice" in df.columns else df.select_dtypes(include=np.number).columns[0]
    K = 400
    df["TOI_Factor"] = df[toi_col] / (df[toi_col] + K)
    df["OWS"] = df["OWS"] * df["TOI_Factor"]
    df["DWS"] = df["DWS"] * df["TOI_Factor"]
    df["WS"] = df["OWS"] + df["DWS"]

    # PERCENTILES & RANKINGS
    for m in ["OWS", "DWS", "WS"]:
        df[f"{m}_percentile"] = df[m].rank(pct=True) * 100
        df[f"{m}_rank"] = df[m].rank(ascending=False, method="min").astype(int)

    return df

# ---------------------------------------------------
# RUN APP
# ---------------------------------------------------
df = load_data()

st.title("🏒 Liiga Player Profiles 2025-2026")

# FILTERS
filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    team_filter = st.selectbox("Select Team", ["All"] + sorted(df["Team"].unique().tolist()))
with filter_col2:
    position_filter = st.selectbox("Select Position", ["All"] + sorted(df["Position"].unique().tolist()))
with filter_col3:
    games_col = "Games_played" if "Games_played" in df.columns else df.select_dtypes(include=np.number).columns[0]
    min_games = st.slider("Minimum Games Played", 1, int(df[games_col].max()), 5)

# APPLY FILTERS
filtered_df = df.copy()
if team_filter != "All":
    filtered_df = filtered_df[filtered_df["Team"] == team_filter]
if position_filter != "All":
    filtered_df = filtered_df[filtered_df["Position"] == position_filter]
if games_col in filtered_df.columns:
    filtered_df = filtered_df[filtered_df[games_col] >= min_games]

# PLAYER SELECTOR
player = st.selectbox("Select Player", sorted(filtered_df["Player"].unique()))
player_df = filtered_df[filtered_df["Player"] == player].iloc[0]

# UI METRICS
st.subheader(f"{player_df['Player']} | {player_df['Team']} | {player_df['Position']}")
col1, col2, col3 = st.columns(3)
col1.metric("OWS", f"{round(player_df['OWS'], 2)} (#{player_df['OWS_rank']})")
col2.metric("DWS", f"{round(player_df['DWS'], 2)} (#{player_df['DWS_rank']})")
col3.metric("WS", f"{round(player_df['WS'], 2)} (#{player_df['WS_rank']})")

# TOP 10
st.subheader("Top 10 Win Shares")
top_ws = filtered_df[["Player", "Team", "Position", "OWS", "DWS", "WS"]].sort_values("WS", ascending=False).head(10)
st.dataframe(top_ws, use_container_width=True, hide_index=True)
