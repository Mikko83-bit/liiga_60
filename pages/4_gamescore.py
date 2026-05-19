# =========================================================
# LIIGA GAME SCORE
# CLEAN FIXED VERSION
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
import plotly.graph_objects as go

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Liiga Game Score",
    page_icon="🏒",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("🏒 Liiga Game Score 2025-2026")

# =========================================================
# FILE
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# =========================================================
# CLEAN COLUMNS
# =========================================================

def clean_columns(df):

    cleaned = []

    for col in df.columns:

        col = str(col)

        col = col.strip()

        col = col.replace(" ", "_")
        col = col.replace("/", "_")
        col = col.replace("%", "perc")
        col = col.replace("-", "_")
        col = col.replace("(", "")
        col = col.replace(")", "")
        col = col.replace(",", "")
        col = col.replace(".", "")
        col = col.replace("'", "")

        cleaned.append(col)

    df.columns = cleaned

    return df

# =========================================================
# PERCENTILE
# =========================================================

def pct(series, value):

    return percentileofscore(
        series,
        value
    )

# =========================================================
# GAUGE
# =========================================================

def make_gauge(title, value, color):

    fig = go.Figure(go.Indicator(

        mode="gauge+number",

        value=value,

        number={
            "font": {"size": 40}
        },

        title={
            "text": title,
            "font": {"size": 24}
        },

        gauge={

            "axis": {
                "range": [0, 100]
            },

            "bar": {
                "color": color
            },

            "bgcolor": "#1f2937",

            "borderwidth": 0,

            "steps": [
                {"range": [0, 100], "color": "#111827"}
            ]

        }

    ))

    fig.update_layout(
        height=280,
        paper_bgcolor="#0b1020",
        font={"color": "white"}
    )

    return fig

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    df = pd.read_excel(
        FILE,
        sheet_name="Skaters"
    )

    df = clean_columns(df)

    # =====================================================
    # TEAM
    # =====================================================

    df["Team"] = (
        df["Team"]
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # NUMERIC COLUMNS
    # =====================================================

    numeric_cols = [

        "Goals",
        "Assists",
        "Shots",
        "Time_on_ice",
        "Penalties_drawn",
        "Penalties",
        "Plusminus_Total",
        "Team_xG_when_on_ice",
        "Opponents_xG_when_on_ice",
        "CORSI_for_perc"

    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    # =====================================================
    # TOI
    # =====================================================

    df["TOI"] = df["Time_on_ice"]

    # =====================================================
    # MINIMUM TOI
    # =====================================================

    df = df[
        df["TOI"] >= 300
    ].copy()

    # =====================================================
    # PER 60
    # =====================================================

    df["Goals60"] = (
        df["Goals"]
        /
        df["TOI"]
    ) * 60

    df["Assists60"] = (
        df["Assists"]
        /
        df["TOI"]
    ) * 60

    df["Shots60"] = (
        df["Shots"]
        /
        df["TOI"]
    ) * 60

    # =====================================================
    # PENALTY DIFFERENTIAL
    # =====================================================

    df["PenaltyDiff"] = (

        df["Penalties_drawn"]

        -

        df["Penalties"]

    )

    df["PenaltyDiff60"] = (

        df["PenaltyDiff"]

        /

        df["TOI"]

    ) * 60

    # =====================================================
    # PLUS MINUS
    # =====================================================

    df["PlusMinus60"] = (

        df["Plusminus_Total"]

        /

        df["TOI"]

    ) * 60

    # =====================================================
    # CORSI DIFFERENTIAL
    # =====================================================

    df["CorsiDiff"] = (

        df["CORSI_for_perc"]

        -

        50

    )

    # =====================================================
    # xGF / xGA
    # =====================================================

    df["xGF60"] = (

        df["Team_xG_when_on_ice"]

        /

        df["TOI"]

    ) * 60

    df["xGA60"] = (

        df["Opponents_xG_when_on_ice"]

        /

        df["TOI"]

    ) * 60

    # =====================================================
    # CLEAN
    # =====================================================

    df = df.replace(
        [np.inf, -np.inf],
        0
    )

    df = df.fillna(0)

    # =====================================================
    # FORWARDS
    # =====================================================

    forwards = df["Position"] == "F"

    df.loc[forwards, "GameScore"] = (

        0.75 * df.loc[forwards, "Goals60"]

        +

        0.625 * df.loc[forwards, "Assists60"]

        +

        0.075 * df.loc[forwards, "Shots60"]

        +

        0.15 * df.loc[forwards, "PenaltyDiff60"]

        +

        0.05 * df.loc[forwards, "CorsiDiff"]

        +

        0.15 * df.loc[forwards, "PlusMinus60"]

        +

        0.625 * df.loc[forwards, "xGF60"]

        -

        1.75 * df.loc[forwards, "xGA60"]

    )

    # =====================================================
    # DEFENSEMEN
    # =====================================================

    defense = df["Position"] == "D"

    df.loc[defense, "GameScore"] = (

        0.75 * df.loc[defense, "Goals60"]

        +

        0.625 * df.loc[defense, "Assists60"]

        +

        0.075 * df.loc[defense, "Shots60"]

        +

        0.15 * df.loc[defense, "PenaltyDiff60"]

        +

        0.05 * df.loc[defense, "CorsiDiff"]

        +

        0.15 * df.loc[defense, "PlusMinus60"]

        +

        1.7 * df.loc[defense, "xGF60"]

        -

        2.3 * df.loc[defense, "xGA60"]

    )

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

    df["GameScore"] = (

        df["GameScore"]

        *

        df["TOI_Factor"]

    )

    return df

# =========================================================
# LOAD
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
# TABLE
# =========================================================

st.subheader("Top Game Scores")

table = (

    filtered_df[[
        "Player",
        "Team",
        "Position",
        "Goals60",
        "Assists60",
        "Shots60",
        "GameScore"
    ]]

    .sort_values(
        "GameScore",
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

st.header("Player Game Score Card")

card_team = st.selectbox(
    "Choose Team",
    sorted(df["Team"].unique())
)

team_players = (

    df[
        df["Team"] == card_team
    ]["Player"]

    .sort_values()

)

selected_player = st.selectbox(
    "Choose Player",
    team_players
)

player = df[
    df["Player"] == selected_player
].iloc[0]

# =========================================================
# PERCENTILE
# =========================================================

gs_pct = pct(
    df["GameScore"],
    player["GameScore"]
)

# =========================================================
# HEADER
# =========================================================

st.subheader(
    f"{player['Player']} | {player['Team']} | {player['Position']}"
)

# =========================================================
# GAUGE
# =========================================================

st.plotly_chart(
    make_gauge(
        "Game Score Percentile",
        round(gs_pct),
        "#8b5cf6"
    ),
    use_container_width=True
)

# =========================================================
# METRICS
# =========================================================

m1, m2, m3, m4, m5, m6 = st.columns(6)

with m1:
    st.metric("Goals/60", round(player["Goals60"], 2))

with m2:
    st.metric("Assists/60", round(player["Assists60"], 2))

with m3:
    st.metric("Shots/60", round(player["Shots60"], 2))

with m4:
    st.metric("PenaltyDiff/60", round(player["PenaltyDiff60"], 2))

with m5:
    st.metric("CorsiDiff", round(player["CorsiDiff"], 2))

with m6:
    st.metric("GameScore", round(player["GameScore"], 2))
