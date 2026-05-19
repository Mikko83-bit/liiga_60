# =========================================================
# LIIGA PLAYER COMPARISON CARDS
# FINAL FIXED VERSION
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Liiga Skill Cards",
    page_icon="🏒",
    layout="wide"
)

# =========================================================
# TITLE
# =========================================================

st.title("🏒 Liiga Skill Comparison")

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

def percentile(series):

    return (
        series.rank(pct=True) * 100
    )

# =========================================================
# LABEL
# =========================================================

def get_label(value):

    if value >= 85:
        return "ELITE"

    elif value >= 70:
        return "EXCELLENT"

    elif value >= 55:
        return "GOOD"

    elif value >= 40:
        return "AVERAGE"

    else:
        return "BELOW AVG"

# =========================================================
# COLOR
# =========================================================

def get_color(value):

    if value >= 70:
        return "#3b82f6"

    elif value >= 40:
        return "#b7d3ea"

    else:
        return "#efb1b1"

# =========================================================
# COMPACT SKILL CARD
# =========================================================

def skill_card(skill, value):

    color = get_color(value)

    label = get_label(value)

    st.markdown(
        f"""
<div style="
background:{color};
padding:12px;
border-radius:8px;
margin-bottom:12px;
text-align:center;
color:black;
height:110px;
display:flex;
flex-direction:column;
justify-content:center;
">

<div style="
font-size:14px;
font-weight:700;
margin-bottom:2px;
">
{skill}
</div>

<div style="
font-size:36px;
font-weight:900;
line-height:1;
">
{int(value)}
</div>

<div style="
font-size:11px;
letter-spacing:1px;
font-weight:700;
margin-top:4px;
">
{label}
</div>

</div>
""",
        unsafe_allow_html=True
    )

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
    # NUMERIC COLUMNS
    # =====================================================

    numeric_cols = [

        "Goals",
        "Assists",
        "First_assist",
        "Shots",
        "Entries",
        "Breakouts",
        "Breakouts_via_pass",
        "Takeaways",
        "Puck_touches",
        "Puck_control_time",
        "Accurate_passes_perc",
        "Team_xG_when_on_ice",
        "Opponents_xG_when_on_ice",
        "NetxG",
        "CORSI_for_perc",
        "Fenwick_for_perc",
        "Time_on_ice"

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
    # FILTER LOW SAMPLE
    # =====================================================

    df = df[
        df["TOI"] >= 300
    ].copy()

    # =====================================================
    # PER60
    # =====================================================

    def per60(stat):

        return (
            df[stat]
            /
            df["TOI"]
        ) * 60

    df["Goals60"] = per60("Goals")

    df["Assists60"] = per60("Assists")

    df["Shots60"] = per60("Shots")

    df["Entries60"] = per60("Entries")

    df["Breakouts60"] = per60("Breakouts")

    df["Takeaways60"] = per60("Takeaways")

    # =====================================================
    # xG
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
    # SHOOTING
    # =====================================================

    df["ShootingRaw"] = (

        0.40 * df["Goals60"]

        +

        0.35 * df["Shots60"]

        +

        0.25 * df["xGF60"]

    )

    # =====================================================
    # PLAYMAKING
    # =====================================================

    df["PlaymakingRaw"] = (

        0.50 * df["Assists60"]

        +

        0.30 * df["First_assist"]

        +

        0.20 * df["Accurate_passes_perc"]

    )

    # =====================================================
    # TRANSITION
    # =====================================================

    df["TransitionRaw"] = (

        0.30 * df["Entries60"]

        +

        0.30 * df["Breakouts60"]

        +

        0.20 * df["Breakouts_via_pass"]

        +

        0.20 * df["Accurate_passes_perc"]

    )

    # =====================================================
    # PUCK MOVEMENT
    # =====================================================

    df["PuckMovementRaw"] = (

        0.50 * df["Puck_touches"]

        +

        0.50 * df["Puck_control_time"]

    )

    # =====================================================
    # DEFENSE
    # =====================================================

    df["DefenseRaw"] = (

        0.50 * df["Takeaways60"]

        -

        0.50 * df["xGA60"]

    )

    # =====================================================
    # IMPACT
    # =====================================================

    df["ImpactRaw"] = (

        0.40 * df["NetxG"]

        +

        0.30 * df["CORSI_for_perc"]

        +

        0.30 * df["Fenwick_for_perc"]

    )

    # =====================================================
    # CATEGORY SCORES
    # =====================================================

    categories = [

        "Shooting",
        "Playmaking",
        "Transition",
        "PuckMovement",
        "Defense",
        "Impact"

    ]

    for cat in categories:

        df[f"{cat}Score"] = percentile(
            df[f"{cat}Raw"]
        )

    # =====================================================
    # OVERALL SCORE
    # =====================================================

    forwards = df["Position"] == "F"

    df.loc[forwards, "OverallScore"] = (

        0.30 * df.loc[forwards, "ShootingScore"]

        +

        0.25 * df.loc[forwards, "PlaymakingScore"]

        +

        0.20 * df.loc[forwards, "TransitionScore"]

        +

        0.15 * df.loc[forwards, "DefenseScore"]

        +

        0.10 * df.loc[forwards, "ImpactScore"]

    )

    defense = df["Position"] == "D"

    df.loc[defense, "OverallScore"] = (

        0.15 * df.loc[defense, "ShootingScore"]

        +

        0.20 * df.loc[defense, "PlaymakingScore"]

        +

        0.25 * df.loc[defense, "TransitionScore"]

        +

        0.30 * df.loc[defense, "DefenseScore"]

        +

        0.10 * df.loc[defense, "ImpactScore"]

    )

    return df

# =========================================================
# LOAD
# =========================================================

df = load_data()

# =========================================================
# PLAYER SELECT
# =========================================================

c1, c2 = st.columns(2)

with c1:

    player1_name = st.selectbox(
        "Player 1",
        sorted(df["Player"].unique())
    )

with c2:

    player2_name = st.selectbox(
        "Player 2",
        sorted(df["Player"].unique()),
        index=1
    )

player1 = df[
    df["Player"] == player1_name
].iloc[0]

player2 = df[
    df["Player"] == player2_name
].iloc[0]

# =========================================================
# HEADER
# =========================================================

h1, h2, h3 = st.columns([5,1,5])

with h1:

    st.markdown(f"""
## {player1['Player']}

{player1['Team']} | {player1['Position']}
""")

with h2:

    st.markdown("## VS")

with h3:

    st.markdown(f"""
## {player2['Player']}

{player2['Team']} | {player2['Position']}
""")

# =========================================================
# SKILLS
# =========================================================

st.markdown("## Skill Comparison")

left, gap, right = st.columns([5,0.5,5])

skills = [

    ("Shooting", "ShootingScore"),
    ("Playmaking", "PlaymakingScore"),
    ("Transition", "TransitionScore"),
    ("Puck Movement", "PuckMovementScore"),
    ("Defense", "DefenseScore"),
    ("Impact", "ImpactScore")

]

with left:

    for label, col in skills:

        skill_card(
            label,
            player1[col]
        )

with right:

    for label, col in skills:

        skill_card(
            label,
            player2[col]
        )

# =========================================================
# OVERALL
# =========================================================

st.divider()

o1, o2 = st.columns(2)

with o1:

    st.metric(
        "Overall",
        round(player1["OverallScore"], 1)
    )

with o2:

    st.metric(
        "Overall",
        round(player2["OverallScore"], 1)
    )
