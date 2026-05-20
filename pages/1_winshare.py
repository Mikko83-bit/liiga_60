import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# STREAMLIT PAGE
# =========================================================

st.set_page_config(
    page_title="Liiga Projection Grades",
    layout="wide"
)

st.title("Liiga Projection Grade Model")

st.write("""
Tämä malli:
- laskee per60-luvut
- vertaa pelaajia liigakeskiarvoon
- muodostaa projection scoren
- muuntaa scoret 4–10 arvosanoiksi
""")

# =========================================================
# LOAD EXCEL
# =========================================================

try:

    df = pd.read_excel(
        "../Liiga 2025-2026_skaters_teams.xlsx"
    )

except Exception as e:

    st.error(f"Excelin lataus epäonnistui: {e}")
    st.stop()

# =========================================================
# NÄYTÄ SARAKKEET DEBUGIA VARTEN
# =========================================================

with st.expander("Näytä datan sarakkeet"):

    st.write(df.columns.tolist())

# =========================================================
# TOI COLUMN
# =========================================================
# VAIHDA TÄMÄ JOS TARPEEN
# =========================================================

TOI_COLUMN = "TOI"

if TOI_COLUMN not in df.columns:

    st.error(
        f"TOI-saraketta '{TOI_COLUMN}' ei löydy datasta."
    )

    st.stop()

# =========================================================
# METRICS
# =========================================================

metrics = [
    "Goals",
    "First assist",
    "xG",
    "Shots",
    "Passes to the slot",
    "Entries",
    "Takeaways",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

# =========================================================
# TARKISTA PUUTTUVAT SARAKKEET
# =========================================================

missing = [
    col for col in metrics
    if col not in df.columns
]

if len(missing) > 0:

    st.error(
        f"Nämä sarakkeet puuttuvat datasta: {missing}"
    )

    st.stop()

# =========================================================
# CLEAN DATA
# =========================================================

df = df.copy()

# Poista rivit ilman TOI:ta
df = df[df[TOI_COLUMN] > 0]

# Täytä puuttuvat arvot nollalla
df[metrics] = df[metrics].fillna(0)

# =========================================================
# PER60
# =========================================================

for metric in metrics:

    df[f"{metric}_per60"] = (
        df[metric] / df[TOI_COLUMN]
    ) * 60

# =========================================================
# LEAGUE AVERAGES
# =========================================================

league_avg = {}

for metric in metrics:

    league_avg[metric] = (
        df[f"{metric}_per60"].mean()
    )

# =========================================================
# DELTA METRICS
# =========================================================

for metric in metrics:

    df[f"d_{metric}"] = (
        df[f"{metric}_per60"]
        - league_avg[metric]
    )

# =========================================================
# PROJECTION SCORE
# =========================================================
# VOIT MUOKATA PAINOJA MYÖHEMMIN
# =========================================================

df["Projection Score"] = (

    0.30 * df["d_Goals"]

    + 0.25 * df["d_First assist"]

    + 0.20 * df["d_xG"]

    + 0.10 * df["d_Passes to the slot"]

    + 0.10 * df["d_Entries"]

    + 0.10 * df["d_Takeaways"]

    - 0.15 * df["d_Puck losses"]

    + 0.20 * df["d_Team xG when on ice"]

    - 0.20 * df["d_Opponent's xG when on ice"]

)

# =========================================================
# PERCENTILE
# =========================================================

df["Percentile"] = (
    df["Projection Score"]
    .rank(pct=True)
) * 100

# =========================================================
# GRADE 4-10
# =========================================================

df["Grade"] = (
    4 + (df["Percentile"] / 100) * 6
).round(1)

# =========================================================
# SORT
# =========================================================

df = df.sort_values(
    by="Grade",
    ascending=False
)

# =========================================================
# PLAYER SELECT
# =========================================================

if "Player" in df.columns:

    player_col = "Player"

else:

    player_col = df.columns[0]

player = st.selectbox(
    "Select Player",
    sorted(df[player_col].unique())
)

player_df = df[
    df[player_col] == player
]

# =========================================================
# PLAYER CARD
# =========================================================

st.subheader(player)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Projection Score",
        round(
            player_df["Projection Score"].iloc[0],
            2
        )
    )

with col2:

    st.metric(
        "Percentile",
        round(
            player_df["Percentile"].iloc[0],
            1
        )
    )

with col3:

    st.metric(
        "Grade",
        player_df["Grade"].iloc[0]
    )

# =========================================================
# UNDERLYING METRICS
# =========================================================

st.subheader("Underlying Metrics")

display_metrics = pd.DataFrame({

    "Metric": metrics,

    "Per60": [
        round(
            player_df[f"{m}_per60"].iloc[0],
            2
        )
        for m in metrics
    ],

    "Delta vs League": [
        round(
            player_df[f"d_{m}"].iloc[0],
            2
        )
        for m in metrics
    ]
})

st.dataframe(
    display_metrics,
    use_container_width=True
)

# =========================================================
# FULL TABLE
# =========================================================

st.subheader("All Players")

show_cols = [
    player_col,
    "Projection Score",
    "Percentile",
    "Grade"
]

st.dataframe(
    df[show_cols],
    use_container_width=True,
    height=700
)
