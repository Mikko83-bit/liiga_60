import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Projection Model",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================
st.title("Projection Model")

st.markdown("""
Projection-oriented player model using:
- Relative production
- Team-adjusted impact
- Sustainable offensive metrics
- Usage-adjusted projection
""")

# =========================================================
# LOAD DATA (Suojattu välimuistilla ja kopioinnilla)
# =========================================================
FILE = "Liiga 2025-2026_skaters_teams.xlsx"

@st.cache_data
def load_raw_data():
    p_df = pd.read_excel(FILE, sheet_name=0)
    t_df = pd.read_excel(FILE, sheet_name=1)
    return p_df, t_df

raw_players, raw_teams = load_raw_data()
df = raw_players.copy()
teams_df = raw_teams.copy()

# =========================================================
# CLEAN COLUMN NAMES & FIX HEADERS
# =========================================================
df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\r", "", regex=False)
)

teams_df.columns = (
    teams_df.columns
    .astype(str)
    .str.strip()
    .str.replace("\n", "", regex=False)
    .str.replace("\r", "", regex=False)
)

# Otsikkokorjaus lennosta jos sarake on "th"
if "th" in df.columns and "Date of birth" not in df.columns:
    df = df.rename(columns={"th": "Date of birth"})

# =========================================================
# VALUVALMIS IÄN LASKENTA (Tehdään ENNEN mitään muuta operaatiota)
# =========================================================
# Muutetaan sarakkeen arvot pd.to_datetime -muotoon, pakotetaan virheet NaT:ksi
parsed_dates = pd.to_datetime(df["Date of birth"], errors="coerce")

# Lasketaan ikä suoraan vuodesta 2026 käsin perustuen syntymävuoteen
df["Age"] = 2026 - parsed_dates.dt.year

# Sateenvarjomekanismi: jos jokin rivi epäonnistui, poimitaan vuosi tekstistä stringinä
backup_years = pd.to_numeric(df["Date of birth"].astype(str).str.extract(r'^(\d{4})')[0], errors="coerce")
df["Age"] = df["Age"].fillna(2026 - backup_years)

# Jos vieläkään ei löydy ikää, annetaan oletus
df["Age"] = df["Age"].fillna(26.0).astype(float)

# =========================================================
# REQUIRED COLUMNS CHECK
# =========================================================
required_player_columns = [
    "Player", "Team", "Position", "Games played", "Time on ice",
    "Goals", "First assist", "xG", "Pre-shots passes", "Team xG when on ice",
    "Opponent's xG when on ice", "Puck losses"
]
required_team_columns = ["Team", "Games", "xGF", "xGA"]

missing_player = [col for col in required_player_columns if col not in df.columns]
missing_team = [col for col in required_team_columns if col not in teams_df.columns]

if len(missing_player) > 0:
    st.error(f"Missing player columns: {missing_player}")
    st.stop()

if len(missing_team) > 0:
    st.error(f"Missing team columns: {missing_team}")
    st.stop()

# =========================================================
# NUMERIC CONVERSION
# =========================================================
player_numeric_cols = [
    "Games played", "Time on ice", "Goals", "First assist", "xG",
    "Pre-shots passes", "Team xG when on ice", "Opponent's xG when on ice", "Puck losses"
]
for col in player_numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

team_numeric_cols = ["Games", "xGF", "xGA"]
for col in team_numeric_cols:
    teams_df[col] = pd.to_numeric(teams_df[col], errors="coerce").fillna(0)

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("Filters")

positions = sorted(df["Position"].dropna().unique())
selected_position = st.sidebar.selectbox("Position", positions)

selected_age = st.sidebar.slider("Maximum Age", 16, 45, 40)
min_toi = st.sidebar.slider("Minimum TOI", 0, 2000, 300, 10)
min_games = st.sidebar.slider("Minimum Games", 0, 80, 10)

# =========================================================
# APPLY FILTERS (Kopioidaan slice omaksi DataFrameksi indeksisotkujen estämiseksi)
# =========================================================
df = df[
    (df["Position"] == selected_position) & 
    (df["Age"] <= selected_age) & 
    (df["Time on ice"] >= min_toi) & 
    (df["Games played"] >= min_games)
].copy()

if len(df) == 0:
    st.warning("No players found with the current filter criteria.")
    st.stop()

# =========================================================
# PER60 METRICS
# =========================================================
per60_metrics = ["Goals", "First assist", "xG", "Pre-shots passes", "Puck losses"]
for metric in per60_metrics:
    df[f"{metric}_per60"] = np.where(df["Time on ice"] > 0, (df[metric] / df["Time on ice"]) * 60, 0)

# =========================================================
# TEAM CONTEXT & MAPS
# =========================================================
teams_df["xGF_per_game"] = np.where(teams_df["Games"] > 0, teams_df["xGF"] / teams_df["Games"], 0)
teams_df["xGA_per_game"] = np.where(teams_df["Games"] > 0, teams_df["xGA"] / teams_df["Games"], 0)

team_xgf_map = dict(zip(teams_df["Team"], teams_df["xGF_per_game"]))
team_xga_map = dict(zip(teams_df["Team"], teams_df["xGA_per_game"]))

# =========================================================
# LEAGUE AVERAGES & DELTAS
# =========================================================
league_avg = {}
league_metrics = ["Goals_per60", "First assist_per60", "xG_per60", "Pre-shots passes_per60", "Puck losses_per60"]

for metric in league_metrics:
    league_avg[metric] = df[metric].mean()

df["dGoals"] = df["Goals_per60"] - league_avg["Goals_per60"]
df["dA1"] = df["First assist_per60"] - league_avg["First assist_per60"]
df["dxG"] = df["xG_per60"] - league_avg["xG_per60"]
df["dPreShots"] = df["Pre-shots passes_per60"] - league_avg["Pre-shots passes_per60"]
df["dPuckLoss"] = league_avg["Puck losses_per60"] - df["Puck losses_per60"]

# RELATIVE TEAM IMPACT
df["Rel xGF"] = df["Team xG when on ice"] - df["Team"].map(team_xgf_map)
df["Rel xGA"] = df["Team"].map(team_xga_map) - df["Opponent's xG when on ice"]

# =========================================================
# PROJECTION SCORE & TOI FACTOR
# =========================================================
df["Projection Raw"] = (
    (0.22 * df["dGoals"])
    + (0.28 * df["dA1"])
    + (0.22 * df["dxG"])
    + (0.18 * df["dPreShots"])
    + (0.12 * df["Rel xGF"])
    + (0.12 * df["Rel xGA"])
    + (0.06 * df["dPuckLoss"])
)

league_avg_toi = df["Time on ice"].mean()
df["TOI Factor"] = np.where(league_avg_toi > 0, np.sqrt(df["Time on ice"] / league_avg_toi), 1.0)
df["Projection Score"] = df["Projection Raw"] * df["TOI Factor"]

# PERCENTILE & GRADE
df["Percentile"] = df["Projection Score"].rank(pct=True) * 100
df["Grade"] = (4 + (df["Percentile"] / 100) * 6).round(1)

# SORT & RANK
df = df.sort_values("Projection Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# =========================================================
# DISPLAY RANKINGS
# =========================================================
st.markdown("## Projection Rankings")

show_cols = [
    "Rank", "Player", "Team", "Age", "Games played", "Time on ice", "Grade",
    "Projection Score", "Percentile", "Goals_per60", "First assist_per60",
    "xG_per60", "Pre-shots passes_per60", "Rel xGF", "Rel xGA"
]

display_df = df[show_cols].copy()
display_df.columns = [
    "Rank", "Player", "Team", "Age", "GP", "TOI", "Grade", "Projection",
    "Percentile", "Goals/60", "A1/60", "xG/60", "PreShots/60", "Rel xGF", "Rel xGA"
]

round_cols = ["Age", "Projection", "Percentile", "Goals/60", "A1/60", "xG/60", "PreShots/60", "Rel xGF", "Rel xGA"]
display_df[round_cols] = display_df[round_cols].round(1)
display_df["TOI"] = display_df["TOI"].round(0).astype(int)
display_df["Age"] = display_df["Age"].astype(int) # Muutetaan kokonaisluvuksi selkeyden vuoksi

st.dataframe(
    display_df,
    use_container_width=True,
    height=900,
    hide_index=True
)
