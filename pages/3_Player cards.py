# =========================================================
# LIIGA STAT CARDS
# FINAL CLEAN VERSION
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.stats import percentileofscore

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Liiga Stat Cards",
    page_icon="🏒",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

html, body, [class*="css"] {
    background-color: #0b1020;
    color: white;
}

.block-container {
    padding-top: 2rem;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================

st.title("🏒 Liiga Stat Cards 2025-2026")

# =========================================================
# FILE
# =========================================================

FILE = "Liiga 2025-2026_skaters_teams.xlsx"

# =========================================================
# CLEAN COLUMNS
# =========================================================

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
        .str.replace(",", "", regex=False)
        .str.replace(".", "", regex=False)

    )

    return df

# =========================================================
# Z SCORE
# =========================================================

def zscore(series):

    std = series.std()

    if std == 0:
        return pd.Series(0, index=series.index)

    z = (series - series.mean()) / std

    return z.clip(-3, 3)

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

    players = pd.read_excel(
        FILE,
        sheet_name="Skaters"
    )

    players = clean_columns(players)

    # =====================================================
    # TEAM CLEAN
    # =====================================================

    players["Team"] = (
        players["Team"]
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # NUMERIC
    # =====================================================

    numeric_cols = [

        "Goals",
        "Assists",
        "xG",
        "Time_on_ice",
        "Passes_to_the_slot",
        "Entries",
        "Breakouts",
        "Takeaways",
        "Puck_losses",
        "Puck_battles_won",
        "NetxG",
        "CORSI_for",
        "Fenwick_for"

    ]

    for col in numeric_cols:

        players[col] = pd.to_numeric(
            players[col],
            errors="coerce"
        ).fillna(0)

    # =====================================================
    # TOI
    # =====================================================

    players["TOI"] = players["Time_on_ice"]

    # =====================================================
    # MINIMUM TOI
    # =====================================================

    players = players[
        players["TOI"] >= 300
    ].copy()

    # =====================================================
    # PER 60
    # =====================================================

    per60_stats = {

        "Goals": "Goals60",
        "Assists": "Assists60",
        "xG": "xG60",
        "Passes_to_the_slot": "SlotPass60",
        "Entries": "Entries60",
        "Breakouts": "Breakouts60",
        "Takeaways": "Takeaways60",
        "Puck_losses": "PuckLoss60",
        "Puck_battles_won": "Battles60"

    }

    for raw, new in per60_stats.items():

        players[new] = (
            players[raw]
            /
            players["TOI"]
        ) * 60

    players = players.replace(
        [np.inf, -np.inf],
        0
    )

    players = players.fillna(0)

    # =====================================================
    # POSITION NORMALIZATION
    # =====================================================

    z_cols = [

        "Goals60",
        "Assists60",
        "xG60",
        "SlotPass60",
        "Entries60",
        "Breakouts60",
        "Takeaways60",
        "PuckLoss60",
        "Battles60",
        "NetxG",
        "CORSI_for",
        "Fenwick_for"

    ]

    for position in ["F", "D"]:

        mask = players["Position"] == position

        for col in z_cols:

            players.loc[mask, f"{col}_z"] = zscore(
                players.loc[mask, col]
            )

    # =====================================================
    # RATINGS
    # =====================================================

    players["OffenseRating"] = (

        0.35 * players["Goals60_z"]

        +

        0.30 * players["Assists60_z"]

        +

        0.20 * players["xG60_z"]

        +

        0.15 * players["SlotPass60_z"]

    )

    players["DefenseRating"] = (

        0.35 * players["NetxG_z"]

        +

        0.25 * players["Takeaways60_z"]

        -

        0.25 * players["PuckLoss60_z"]

        +

        0.15 * players["Battles60_z"]

    )

    players["TransitionRating"] = (

        0.50 * players["Entries60_z"]

        +

        0.50 * players["Breakouts60_z"]

    )

    players["PossessionRating"] = (

        0.50 * players["CORSI_for_z"]

        +

        0.50 * players["Fenwick_for_z"]

    )

    players["OverallRating"] = (

        0.35 * players["OffenseRating"]

        +

        0.30 * players["DefenseRating"]

        +

        0.20 * players["TransitionRating"]

        +

        0.15 * players["PossessionRating"]

    )

    # =====================================================
    # TOI STABILIZATION
    # =====================================================

    K = 400

    players["TOI_Factor"] = (

        players["TOI"]

        /

        (
            players["TOI"] + K
        )

    )

    rating_cols = [

        "OffenseRating",
        "DefenseRating",
        "TransitionRating",
        "PossessionRating",
        "OverallRating"

    ]

    for col in rating_cols:

        players[col] = (
            players[col]
            *
            players["TOI_Factor"]
        )

    return players

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
# TOP TABLE
# =========================================================

st.subheader("Top Overall Ratings")

table = (

    filtered_df[[
        "Player",
        "Team",
        "Position",
        "OffenseRating",
        "DefenseRating",
        "TransitionRating",
        "OverallRating"
    ]]

    .sort_values(
        "OverallRating",
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

st.header("Player Stat Card")

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
# HEADER
# =========================================================

st.subheader(
    f"{player['Player']} | {player['Team']} | {player['Position']}"
)

# =========================================================
# PERCENTILES
# =========================================================

off_pct = pct(
    df["OffenseRating"],
    player["OffenseRating"]
)

def_pct = pct(
    df["DefenseRating"],
    player["DefenseRating"]
)

trans_pct = pct(
    df["TransitionRating"],
    player["TransitionRating"]
)

overall_pct = pct(
    df["OverallRating"],
    player["OverallRating"]
)

# =========================================================
# GAUGES
# =========================================================

g1, g2, g3, g4 = st.columns(4)

with g1:

    st.plotly_chart(
        make_gauge(
            "Offense",
            round(off_pct),
            "#3b82f6"
        ),
        use_container_width=True
    )

with g2:

    st.plotly_chart(
        make_gauge(
            "Defense",
            round(def_pct),
            "#f97316"
        ),
        use_container_width=True
    )

with g3:

    st.plotly_chart(
        make_gauge(
            "Transition",
            round(trans_pct),
            "#10b981"
        ),
        use_container_width=True
    )

with g4:

    st.plotly_chart(
        make_gauge(
            "Overall",
            round(overall_pct),
            "#a855f7"
        ),
        use_container_width=True
    )

# =========================================================
# PLAYER METRICS
# =========================================================

st.subheader("Player Metrics")

s1, s2, s3, s4, s5, s6 = st.columns(6)

with s1:
    st.metric("Goals", round(player["Goals"], 1))

with s2:
    st.metric("Assists", round(player["Assists"], 1))

with s3:
    st.metric("xG", round(player["xG"], 2))

with s4:
    st.metric("NetxG", round(player["NetxG"], 2))

with s5:
    st.metric("Entries/60", round(player["Entries60"], 2))

with s6:
    st.metric("Breakouts/60", round(player["Breakouts60"], 2))
