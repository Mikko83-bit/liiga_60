import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Projection Model", layout="wide")
st.title("Projection Model & Data Debugger")

# =========================================================
# LOAD DATA
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

# Siivotaan sarakkeiden nimet kaikesta ylimääräisestä tyhjästä
df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
teams_df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in teams_df.columns]

# =========================================================
# DIAGNOSTIIKKA-IKKUNA (Näkyy vain sovelluksen ylälaidassa)
# =========================================================
st.subheader("Data Debugger: Excelin todelliset sarakkeet")
st.write("Alta näet, mitä sarakkeita koodi löysi Excelistäsi ja miltä ensimmäinen rivi näyttää:")
st.dataframe(df.head(2))

# Etsitään oikea sarake lennosta, vaikka nimi olisi vähän sinne päin
dob_col = None
potential_dob_names = ["Date of birth", "DOB", "Syntymäaika", "Syntynyt", "bday", "th"]

for name in potential_dob_names:
    # Etsitään osumaa, joka vastaa osittain tai kokonaan jotain tunnettua nimeä
    found = [col for col in df.columns if name.lower() in col.lower()]
    if found:
        # Varmistetaan, ettei kyseessä ole pelinumero (yleensä "#" tai "No")
        if found[0] not in ["#", "No", "Jersey", "Pelinumero"]:
            dob_col = found[0]
            break

# Jos automaattihaku ei löytänyt mitään, otetaan manuaalisesti kantaa
if not dob_col:
    # Jos sarakkeissa on jotain outoa, yritetään arvata datatyypin perusteella
    for col in df.columns:
        if df[col].astype(str).str.contains(r'\d{4}-\d{2}-\d{2}|\.\d{4}').any():
            dob_col = col
            break

if dob_col:
    st.success(f"Koodi valitsi syntymäaikasarakkeeksi: **'{dob_col}'**")
else:
    st.error("Syntymäaikasaraketta ei löytynyt automaattisesti! Tarkista debuggerin taulukosta oikea sarakenimi.")
    st.stop()

# =========================================================
# IÄN LASKENTA LUOTETTAVASTI OIKEASTA SARAKKEESTA
# =========================================================
# Muutetaan valitun sarakkeen data datetime-muotoon
parsed_dates = pd.to_datetime(df[dob_col], errors="coerce")

# Jos muunnos onnistui, lasketaan ikä vuodesta 2026
df["Age"] = 2026 - parsed_dates.dt.year

# Hätävara tekstimuotoisille vuosille (esim. jos solussa lukee vain "1995")
backup_years = pd.to_numeric(df[dob_col].astype(str).str.extract(r'(\d{4})')[0], errors="coerce")
df["Age"] = df["Age"].fillna(2026 - backup_years)

# Lopullinen hätävara jos data oli korruptoitunut tällä rivillä
df["Age"] = df["Age"].fillna(25).astype(int)

# Varmistetaan, ettei ikä ole mahdoton (esim. pelinumerosta tullut 2000+ vuosi)
df["Age"] = np.where((df["Age"] < 15) | (df["Age"] > 50), 25, df["Age"])

# =========================================================
# REQUIRED COLUMNS CHECK (Poistettu tiukka Date of birth -vaatimus koska se haettiin lennosta)
# =========================================================
required_player_columns = ["Player", "Team", "Position", "Games played", "Time on ice"]
missing_player = [col for col in required_player_columns if col not in df.columns]

if missing_player:
    st.error(f"Missing player columns: {missing_player}")
    st.stop()

# =========================================================
# NUMERIC CONVERSION & CLEANING
# =========================================================
player_numeric_cols = [
    "Games played", "Time on ice", "Goals", "First assist", "xG",
    "Pre-shots passes", "Team xG when on ice", "Opponent's xG when on ice", "Puck losses"
]
for col in player_numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    else:
        df[col] = 0.0

# Tiimitiedot
if "Team" in teams_df.columns:
    for col in ["Games", "xGF", "xGA"]:
        if col in teams_df.columns:
            teams_df[col] = pd.to_numeric(teams_df[col], errors="coerce").fillna(0)
        else:
            teams_df[col] = 0.0

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("Filters")
positions = sorted(df["Position"].dropna().unique()) if "Position" in df.columns else ["F", "D"]
selected_position = st.sidebar.selectbox("Position", positions)

selected_age = st.sidebar.slider("Maximum Age", 16, 45, 45)
min_toi = st.sidebar.slider("Minimum TOI", 0, 2000, 300, 10)
min_games = st.sidebar.slider("Minimum Games", 0, 80, 10)

# Apply filters
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
# METRICS & PROJECTION LASKENTA
# =========================================================
per60_metrics = ["Goals", "First assist", "xG", "Pre-shots passes", "Puck losses"]
for metric in per60_metrics:
    df[f"{metric}_per60"] = np.where(df["Time on ice"] > 0, (df[metric] / df["Time on ice"]) * 60, 0)

if "Games" in teams_df.columns:
    teams_df["xGF_per_game"] = np.where(teams_df["Games"] > 0, teams_df["xGF"] / teams_df["Games"], 0)
    teams_df["xGA_per_game"] = np.where(teams_df["Games"] > 0, teams_df["xGA"] / teams_df["Games"], 0)
    team_xgf_map = dict(zip(teams_df["Team"], teams_df["xGF_per_game"]))
    team_xga_map = dict(zip(teams_df["Team"], teams_df["xGA_per_game"]))
else:
    team_xgf_map, team_xga_map = {}, {}

league_avg = {}
league_metrics = ["Goals_per60", "First assist_per60", "xG_per60", "Pre-shots passes_per60", "Puck losses_per60"]
for metric in league_metrics:
    league_avg[metric] = df[metric].mean()

df["dGoals"] = df["Goals_per60"] - league_avg["Goals_per60"]
df["dA1"] = df["First assist_per60"] - league_avg["First assist_per60"]
df["dxG"] = df["xG_per60"] - league_avg["xG_per60"]
df["dPreShots"] = df["Pre-shots passes_per60"] - league_avg["Pre-shots passes_per60"]
df["dPuckLoss"] = league_avg["Puck losses_per60"] - df["Puck losses_per60"]

df["Rel xGF"] = df["Team xG when on ice"] - df["Team"].map(team_xgf_map).fillna(0)
df["Rel xGA"] = df["Team"].map(team_xga_map).fillna(0) - df["Opponent's xG when on ice"]

df["Projection Raw"] = (
    (0.22 * df["dGoals"]) + (0.28 * df["dA1"]) + (0.22 * df["dxG"]) + 
    (0.18 * df["dPreShots"]) + (0.12 * df["Rel xGF"]) + (0.12 * df["Rel xGA"]) + 
    (0.06 * df["dPuckLoss"])
)

league_avg_toi = df["Time on ice"].mean()
df["TOI Factor"] = np.where(league_avg_toi > 0, np.sqrt(df["Time on ice"] / league_avg_toi), 1.0)
df["Projection Score"] = df["Projection Raw"] * df["TOI Factor"]

df["Percentile"] = df["Projection Score"].rank(pct=True) * 100
df["Grade"] = (4 + (df["Percentile"] / 100) * 6).round(1)

df = df.sort_values("Projection Score", ascending=False).reset_index(drop=True)
df["Rank"] = df.index + 1

# =========================================================
# DISPLAY
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

round_cols = ["Projection", "Percentile", "Goals/60", "A1/60", "xG/60", "PreShots/60", "Rel xGF", "Rel xGA"]
display_df[round_cols] = display_df[round_cols].round(1)
display_df["TOI"] = display_df["TOI"].round(0).astype(int)
display_df["Age"] = display_df["Age"].astype(int)

st.dataframe(display_df, use_container_width=True, height=600, hide_index=True)
