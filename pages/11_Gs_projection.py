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
# LOAD DATA
# =========================================================
FILE = "Liiga 2025-2026_skaters_teams.xlsx"

@st.cache_data
def load_clean_data():
    p_df = pd.read_excel(FILE, sheet_name=0)
    t_df = pd.read_excel(FILE, sheet_name=1)
    return p_df, t_df

try:
    raw_players, raw_teams = load_clean_data()
    df = raw_players.copy()
    teams_df = raw_teams.copy()
except Exception as e:
    st.error(f"Tiedoston luku epäonnistui: {e}")
    st.stop()

# Siivotaan sarakkeiden nimet tyhjistä väleistä ja rivinvahdoista
df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in df.columns]
teams_df.columns = [str(c).strip().replace("\n", "").replace("\r", "") for c in teams_df.columns]

# =========================================================
# ÄLYKÄS SARAKKEIDEN METSÄSTYS SISÄLLÖN PERUSTEELLA
# =========================================================
st.subheader("⚙️ Automaattinen sarakkeiden täsmäytys")

# 1. Etsitään pelipaikka (sarake, jossa on arvoja 'D', 'F', 'D/F')
pos_col = None
for col in df.columns:
    unique_vals = set(df[col].dropna().astype(str).unique())
    if any(p in unique_vals for p in ['D', 'F', 'D/F']):
        pos_col = col
        break
if not pos_col:
    pos_col = "Position" if "Position" in df.columns else df.columns[4]

# 2. Etsitään pelaajan nimi ja joukkue
player_col = [c for c in df.columns if "player" in str(c).lower() or c == "Player"]
player_col = player_col[0] if player_col else df.columns[1]

team_col = [c for c in df.columns if "team" in str(c).lower() or c == "Team"]
team_col = team_col[0] if team_col else df.columns[2]

st.write(f"• Pelaajasarake: `{player_col}`")
st.write(f"• Joukkuesarake: `{team_col}`")
st.write(f"• Pelipaikkasarake: `{pos_col}`")

# =========================================================
# NIMIEN VAIHTO JA NUMEERISTEN SARAKKEIDEN HAKU
# =========================================================
df = df.rename(columns={player_col: "Player", team_col: "Team", pos_col: "Position"})

# Etsitään muut kriittiset sarakkeet nimen perusteella shiftien estämiseksi
toi_col = [c for c in df.columns if "time on ice" in str(c).lower() or "toi" in str(c).lower()][0]
games_col = [c for c in df.columns if "games" in str(c).lower() or "gp" in str(c).lower()][0]
goals_col = [c for c in df.columns if "goals" in str(c).lower() or c == "Goals"][0]
assist_col = [c for c in df.columns if "first assist" in str(c).lower() or "assists" in str(c).lower()][0]
xg_col = [c for c in df.columns if "xg" in str(c).lower() == "xg" or c == "xG"][0]
preshot_col = [c for c in df.columns if "pre-shots passes" in str(c).lower() or "preshot" in str(c).lower() or "passes" in str(c).lower()][0]
puckloss_col = [c for c in df.columns if "puck losses" in str(c).lower() or "losses" in str(c).lower()][0]

df["GP_clean"] = pd.to_numeric(df[games_col], errors="coerce").fillna(0)
df["TOI_clean"] = pd.to_numeric(df[toi_col], errors="coerce").fillna(0)
df["Goals_clean"] = pd.to_numeric(df[goals_col], errors="coerce").fillna(0)
df["A1_clean"] = pd.to_numeric(df[assist_col], errors="coerce").fillna(0)
df["xG_clean"] = pd.to_numeric(df[xg_col], errors="coerce").fillna(0)
df["PreShot_clean"] = pd.to_numeric(df[preshot_col], errors="coerce").fillna(0)
df["PuckLoss_clean"] = pd.to_numeric(df[puckloss_col], errors="coerce").fillna(0)

# =========================================================
# MODEL LOGIC & PER 60 METRICS (Lasketaan globaalisti koko liigasta)
# =========================================================
df["Goals_per60"] = np.where(df["TOI_clean"] > 0, (df["Goals_clean"] / df["TOI_clean"]) * 60, 0)
df["A1_per60"] = np.where(df["TOI_clean"] > 0, (df["A1_clean"] / df["TOI_clean"]) * 60, 0)
df["xG_per60"] = np.where(df["TOI_clean"] > 0, (df["xG_clean"] / df["TOI_clean"]) * 60, 0)
df["PreShot_per60"] = np.where(df["TOI_clean"] > 0, (df["PreShot_clean"] / df["TOI_clean"]) * 60, 0)
df["PuckLoss_per60"] = np.where(df["TOI_clean"] > 0, (df["PuckLoss_clean"] / df["TOI_clean"]) * 60, 0)

# Lasketaan erotukset (Deltat) suhteessa koko liigan keskiarvoon
df["dGoals"] = df["Goals_per60"] - df["Goals_per60"].mean()
df["dA1"] = df["A1_per60"] - df["A1_per60"].mean()
df["dxG"] = df["xG_per60"] - df["xG_per60"].mean()
df["dPreShots"] = df["PreShot_per60"] - df["PreShot_per60"].mean()
df["dPuckLoss"] = df["PuckLoss_per60"].mean() - df["PuckLoss_per60"]

# Painotettu raakapistemäärä
df["Projection Score"] = (
    (0.25 * df["dGoals"]) + 
    (0.30 * df["dA1"]) + 
    (0.25 * df["dxG"]) + 
    (0.15 * df["dPreShots"]) + 
    (0.05 * df["dPuckLoss"])
)

# Peliajan painotuskerroin (TOI Factor)
league_avg_toi = df["TOI_clean"].mean()
df["TOI Factor"] = np.where(league_avg_toi > 0, np.sqrt(df["TOI_clean"] / league_avg_toi), 1.0)
df["Projection Score"] = df["Projection Score"] * df["TOI Factor"]

# Prosenttipisteet ja arvosanat (Grade 4-10) globaalisti koko liigan pohjalta
df["Percentile"] = df["Projection Score"].rank(pct=True) * 100
df["Grade"] = (4 + (df["Percentile"] / 100) * 6).round(1)

# =========================================================
# SIDEBAR FILTERS (Vain Pelipaikka ja Peliaika)
# =========================================================
st.sidebar.header("Suodattimet")

if "Position" in df.columns:
    pos_list = sorted(df["Position"].dropna().unique())
    selected_pos = st.sidebar.selectbox("Pelipaikka", pos_list, index=0)
    filtered_df = df[df["Position"] == selected_pos].copy()
else:
    filtered_df = df.copy()

min_toi = st.sidebar.slider("Minuuttiraja (TOI)", 0, 2000, 300, 10)
filtered_df = filtered_df[filtered_df["TOI_clean"] >= min_toi].copy()

# Järjestetään tulokset parhaasta huonoimpaan ja luodaan sijoitus (Rank)
filtered_df = filtered_df.sort_values("Projection Score", ascending=False).reset_index(drop=True)
filtered_df["Rank"] = filtered_df.index + 1

# =========================================================
# DISPLAY RANKINGS (Ilman ikää)
# =========================================================
st.markdown("## Lopulliset Tulokset")

display_cols = {
    "Rank": "Rank",
    "Player": "Pelaaja",
    "Team": "Joukkue",
    "GP_clean": "GP",
    "TOI_clean": "TOI",
    "Grade": "Arvosana",
    "Projection Score": "Pisteet",
    "Goals_per60": "G/60",
    "A1_per60": "A1/60",
    "xG_per60": "xG/60"
}

out_df = filtered_df[list(display_cols.keys())].copy()
out_df.columns = list(display_cols.values())

# Pyöristetään numeeriset arvot siisteiksi desimaaleiksi
round_targets = ["Pisteet", "G/60", "A1/60", "xG/60"]
out_df[round_targets] = out_df[round_targets].round(2)
out_df["TOI"] = out_df["TOI"].round(0).astype(int)

st.dataframe(
    out_df, 
    use_container_width=True, 
    height=750, 
    hide_index=True
)
