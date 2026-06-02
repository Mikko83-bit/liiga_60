import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Projection Model", layout="wide")
st.title("Projection Model (Column-Shift Proof)")

# =========================================================
# LOAD DATA
# =========================================================
FILE = "Liiga 2025-2026_skaters_teams.xlsx"

@st.cache_data
def load_clean_data():
    p_df = pd.read_excel(FILE, sheet_name=0)
    t_df = pd.read_excel(FILE, sheet_name=1)
    return p_df, t_df

raw_players, raw_teams = load_clean_data()
df = raw_players.copy()
teams_df = raw_teams.copy()

# =========================================================
# ÄLYKÄS SARAKKEIDEN METSÄSTYS SISÄLLÖN PERUSTEELLA
# =========================================================
st.subheader("⚙️ Automaattinen sarakkeiden täsmäytys")

# 1. Etsitään syntymäaika (etsitään sarake, jossa on vähintään yksi nelinumeroinen vuosiluku tai bday-muoto)
dob_col = None
for col in df.columns:
    col_str = df[col].astype(str)
    # Jos solussa on viiva ja 4 numeroa (esim 1995-08-28) tai pisteitä
    if col_str.str.contains(r'\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}').any():
        dob_col = col
        break

# Varajärjestelmä nimen perusteella jos sisältöhaku pettää
if not dob_col:
    for name in ["date of birth", "dob", "syntymäaika", "syntynyt", "th"]:
        found = [c for c in df.columns if name.lower() in str(c).lower()]
        if found:
            dob_col = found[0]
            break

# 2. Etsitään pelipaikka (sarake, jossa on arvoja 'D', 'F', 'H', 'P')
pos_col = None
for col in df.columns:
    unique_vals = set(df[col].dropna().astype(str).unique())
    if any(p in unique_vals for p in ['D', 'F', 'D/F']):
        pos_col = col
        break
if not pos_col:
    pos_col = "Position" if "Position" in df.columns else df.columns[4]

# 3. Etsitään pelaajan nimi ja joukkue
player_col = [c for c in df.columns if "player" in str(c).lower()]
player_col = player_col[0] if player_col else df.columns[1]

team_col = [c for c in df.columns if "team" in str(c).lower()]
team_col = team_col[0] if team_col else df.columns[2]

st.write(f"• Pelaajasarake: `{player_col}`")
st.write(f"• Joukkuesarake: `{team_col}`")
st.write(f"• Pelipaikkasarake: `{pos_col}`")
st.write(f"• Syntymäaikasarake: `{dob_col}`")

# =========================================================
# IÄN LASKENTA LUOTETTAVASTI
# =========================================================
if dob_col:
    parsed_dates = pd.to_datetime(df[dob_col], errors="coerce")
    df["Calculated_Age"] = 2026 - parsed_dates.dt.year
    
    # Backup haku tekstistä jos muunnos epäonnistui
    backup_years = pd.to_numeric(df[dob_col].astype(str).str.extract(r'(\d{4})')[0], errors="coerce")
    df["Calculated_Age"] = df["Calculated_Age"].fillna(2026 - backup_years)
else:
    df["Calculated_Age"] = 25

# Pakotetaan järkevät rajat (jos siirtymä otti pelinumeron tai xG:n, korjataan oletukseksi 25)
df["Calculated_Age"] = df["Calculated_Age"].fillna(25)
df["Calculated_Age"] = np.where((df["Calculated_Age"] < 15) | (df["Calculated_Age"] > 48), 25, df["Calculated_Age"])
df["Calculated_Age"] = df["Calculated_Age"].astype(int)

# =========================================================
# VIRTUAALINEN NIMIEN KORJAUS LASKENTOJA VARTEN
# =========================================================
# Mapataan kriittiset sarakkeet koodin ymmärtämille nimille
rename_dict = {
    player_col: "Player",
    team_col: "Team",
    pos_col: "Position"
}
df = df.rename(columns=rename_dict)

# Varmistetaan muiden numeeristen sarakkeiden haku nimen perusteella
def find_numeric_col(df, standard_name, default_idx):
    found = [c for c in df.columns if standard_name.lower() in str(c).lower()]
    return found[0] if found else df.columns[default_idx]

games_col = find_numeric_col(df, "Games played", 5)
toi_col = find_numeric_col(df, "Time on ice", 6)
goals_col = find_numeric_col(df, "Goals", 7)
assist_col = find_numeric_col(df, "First assist", 9)
xg_col = find_numeric_col(df, "xG", 13)
preshot_col = find_numeric_col(df, "Pre-shots passes", 20)
puckloss_col = find_numeric_col(df, "Puck losses", 25)

# Muutetaan tyypit numeerisiksi turvallisesti
df["GP_clean"] = pd.to_numeric(df[games_col], errors="coerce").fillna(0)
df["TOI_clean"] = pd.to_numeric(df[toi_col], errors="coerce").fillna(0)
df["Goals_clean"] = pd.to_numeric(df[goals_col], errors="coerce").fillna(0)
df["A1_clean"] = pd.to_numeric(df[assist_col], errors="coerce").fillna(0)
df["xG_clean"] = pd.to_numeric(df[xg_col], errors="coerce").fillna(0)
df["PreShot_clean"] = pd.to_numeric(df[preshot_col], errors="coerce").fillna(0)
df["PuckLoss_clean"] = pd.to_numeric(df[puckloss_col], errors="coerce").fillna(0)

# =========================================================
# LEAGUE AVERAGES & DELTAS
# =========================================================
df["Goals_per60"] = np.where(df["TOI_clean"] > 0, (df["Goals_clean"] / df["TOI_clean"]) * 60, 0)
df["A1_per60"] = np.where(df["TOI_clean"] > 0, (df["A1_clean"] / df["TOI_clean"]) * 60, 0)
df["xG_per60"] = np.where(df["TOI_clean"] > 0, (df["xG_clean"] / df["TOI_clean"]) * 60, 0)
df["PreShot_per60"] = np.where(df["TOI_clean"] > 0, (df["PreShot_clean"] / df["TOI_clean"]) * 60, 0)
df["PuckLoss_per60"] = np.where(df["TOI_clean"] > 0, (df["PuckLoss_clean"] / df["TOI_clean"]) * 60, 0)

# Deltojen laskenta koko liigasta
df["dGoals"] = df["Goals_per60"] - df["Goals_per60"].mean()
df["dA1"] = df["A1_per60"] - df["A1_per60"].mean()
df["dxG"] = df["xG_per60"] - df["xG_per60"].mean()
df["dPreShots"] = df["PreShot_per60"] - df["PreShot_per60"].mean()
df["dPuckLoss"] = df["PuckLoss_per60"].mean() - df["PuckLoss_per60"]

# Puhdas ja vakaa kaava ilman siirtyviä joukkuetietoja
df["Projection Score"] = (
    (0.25 * df["dGoals"]) + (0.30 * df["dA1"]) + (0.25 * df["dxG"]) + 
    (0.15 * df["dPreShots"]) + (0.05 * df["dPuckLoss"])
)

# Painotetaan peliajan mukaan
league_avg_toi = df["TOI_clean"].mean()
df["TOI Factor"] = np.where(league_avg_toi > 0, np.sqrt(df["TOI_clean"] / league_avg_toi), 1.0)
df["Projection Score"] = df["Projection Score"] * df["TOI Factor"]

# Prosenttipisteet ja arvosanat globaalisti
df["Percentile"] = df["Projection Score"].rank(pct=True) * 100
df["Grade"] = (4 + (df["Percentile"] / 100) * 6).round(1)

# =========================================================
# SIDEBAR FILTERS
# =========================================================
st.sidebar.header("Suodattimet")

if "Position" in df.columns:
    pos_list = sorted(df["Position"].dropna().unique())
    selected_pos = st.sidebar.selectbox("Pelipaikka", pos_list, index=0)
    filtered_df = df[df["Position"] == selected_pos].copy()
else:
    filtered_df = df.copy()

selected_age = st.sidebar.slider("Maksimi-ikä", 16, 45, 45)
min_toi = st.sidebar.slider("Minuutti-raja (TOI)", 0, 2000, 300, 10)

filtered_df = filtered_df[
    (filtered_df["Calculated_Age"] <= selected_age) & 
    (filtered_df["TOI_clean"] >= min_toi)
].copy()

# Järjestys
filtered_df = filtered_df.sort_values("Projection Score", ascending=False).reset_index(drop=True)
filtered_df["Rank"] = filtered_df.index + 1

# =========================================================
# DISPLAY RANKINGS
# =========================================================
st.markdown("## Lopulliset Tulokset")

display_cols = {
    "Rank": "Rank",
    "Player": "Pelaaja",
    "Team": "Joukkue",
    "Calculated_Age": "Ikä",
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

# Pyöristykset siistiä ulkoasua varten
round_targets = ["Pisteet", "G/60", "A1/60", "xG/60"]
out_df[round_targets] = out_df[round_targets].round(2)
out_df["TOI"] = out_df["TOI"].round(0).astype(int)
out_df["Ikä"] = out_df["Ikä"].astype(int)

st.dataframe(out_df, use_container_width=True, height=600, hide_index=True)
