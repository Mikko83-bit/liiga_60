# =========================================================
# LIIGA STAT CARDS
# Modern Hockey Analytics Card
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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

.card {
    background-color: #121a2b;
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
    border: 1px solid #1f2b45;
}

.metric-title {
    font-size: 15px;
    color: #9ca3af;
    text-align: center;
}

.metric-value {
    font-size: 34px;
    font-weight: 700;
    text-align: center;
}

.small-stat {
    background-color: #121a2b;
    border-radius: 16px;
    padding: 12px;
    text-align: center;
    border: 1px solid #1f2b45;
}

.small-stat-value {
    font-size: 24px;
    font-weight: 700;
}

.small-stat-label {
    color: #9ca3af;
    font-size: 12px;
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
# HELPERS
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


def percentile(series, value):

    return percentileofscore(
        series,
        value
    )


def make_gauge(title, value, color):

    fig = go.Figure(go.Indicator(

        mode="gauge+number",

        value=value,

        number={
            "suffix": "",
            "font": {"size": 42}
        },

        title={
            "text": title,
            "font": {"size": 22}
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
        height=300,
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

    players["Team"] = (
        players["Team"]
        .astype(str)
        .str.strip()
    )

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

    players["TOI"] = players["TOI"].replace(0, np.nan)

    # =====================================================
    # PER 60
    # =====================================================

    per60_cols = {

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

    for raw, new in per60_cols.items():

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
    # RATINGS
    # =====================================================

    # OFFENSE

    players["OffenseRating"] = (

        0.35 * players["Goals60"]

        +

        0.30 * players["Assists60"]

        +

        0.20 * players["xG60"]

        +

        0.15 * players["SlotPass60"]

    )

    # DEFENSE

    players["DefenseRating"] = (

        0.35 * players["NetxG"]

        +

        0.25 * players["Takeaways60"]

        -

        0.20 * players["PuckLoss60"]

        +

        0.20 * players["Battles60"]

    )

    # TRANSITION

    players["TransitionRating"] = (

        0.50 * players["Entries60"]

        +

        0.50 * players["Breakouts60"]

    )

    # POSSESSION

    players["PossessionRating"] = (

        0.50 * players["CORSI_for"]

        +

        0.50 * players["Fenwick_for"]

    )

    # =====================================================
    # OVERALL
    # =====================================================

    players["OverallRating"] = (

        0.35 * players["OffenseRating"]

        +

        0.30 * players["DefenseRating"]

        +

        0.20 * players["TransitionRating"]

        +

        0.15 * players["PossessionRating"]

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
# TOP PLAYERS
# =========================================================

st.subheader("Top Overall Ratings")

top_table = (

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
    top_table,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# PLAYER CARD
# =========================================================

st.divider()

st.header("Player Stat Card")

# TEAM FILTER FOR PLAYER SEARCH

team_card_filter = st.selectbox(
    "Choose Team",
    sorted(df["Team"].unique())
)

team_players = (

    df[
        df["Team"] == team_card_filter
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

st.markdown(f"""
<div class="card">

<h1 style="margin-bottom:0px;">
{player['Player']}
</h1>

<p style="color:#9ca3af;font-size:18px;">
{player['Team']} • {player['Position']}
</p>

</div>
""", unsafe_allow_html=True)

# =========================================================
# PERCENTILES
# =========================================================

off_pct = percentile(
    df["OffenseRating"],
    player["OffenseRating"]
)

def_pct = percentile(
    df["DefenseRating"],
    player["DefenseRating"]
)

trans_pct = percentile(
    df["TransitionRating"],
    player["TransitionRating"]
)

overall_pct = percentile(
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
            "#a78bfa"
        ),
        use_container_width=True
    )

# =========================================================
# SMALL STATS
# =========================================================

st.subheader("Player Metrics")

s1, s2, s3, s4, s5, s6 = st.columns(6)

stats = [

    ("TOI", round(player["TOI"], 1)),
    ("Goals", round(player["Goals"], 1)),
    ("Assists", round(player["Assists"], 1)),
    ("xG", round(player["xG"], 2)),
    ("NetxG", round(player["NetxG"], 2)),
    ("Corsi", round(player["CORSI_for"], 1))

]

for col, (label, value) in zip(
    [s1, s2, s3, s4, s5, s6],
    stats
):

    with col:

        st.markdown(f"""
        <div class="small-stat">

        <div class="small-stat-value">
        {value}
        </div>

        <div class="small-stat-label">
        {label}
        </div>

        </div>
        """, unsafe_allow_html=True)

# =========================================================
# PER 60 TABLE
# =========================================================

st.subheader("Per 60 Statistics")

per60_table = pd.DataFrame({

    "Metric": [

        "Goals/60",
        "Assists/60",
        "xG/60",
        "Entries/60",
        "Breakouts/60",
        "Takeaways/60",
        "Puck Losses/60"

    ],

    "Value": [

        round(player["Goals60"], 2),
        round(player["Assists60"], 2),
        round(player["xG60"], 2),
        round(player["Entries60"], 2),
        round(player["Breakouts60"], 2),
        round(player["Takeaways60"], 2),
        round(player["PuckLoss60"], 2)

    ]

})

st.dataframe(
    per60_table,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# DISTRIBUTION
# =========================================================

st.subheader("Overall Rating Distribution")

fig = px.histogram(
    df,
    x="OverallRating",
    nbins=40
)

fig.update_layout(
    paper_bgcolor="#0b1020",
    plot_bgcolor="#0b1020",
    font_color="white"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
