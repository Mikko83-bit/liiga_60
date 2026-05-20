import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Liiga Projection Grades",
    layout="wide"
)

st.title("Liiga Projection Grade Model")

st.write("""
Model:
- Reads Liiga raw Excel data
- Calculates per60 metrics
- Uses league-relative deltas
- Builds weighted projection score
- Converts scores to 4–10 grades
- Includes player comparison spider chart
""")

# =========================================================
# FILE UPLOADER
# =========================================================

uploaded_file = st.file_uploader(
    "Upload Liiga Excel File",
    type=["xlsx"]
)

if uploaded_file is None:

    st.info("Upload your Excel file.")
    st.stop()

# =========================================================
# READ EXCEL
# =========================================================

try:

    df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(f"Excel loading failed: {e}")
    st.stop()

# =========================================================
# CLEAN COLUMNS
# =========================================================

df.columns = df.columns.str.strip()

# =========================================================
# REQUIRED COLUMNS
# =========================================================

required_columns = [
    "Player",
    "Team",
    "Position",
    "Time on ice",
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

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if len(missing_columns) > 0:

    st.error(f"Missing columns: {missing_columns}")
    st.stop()

# =========================================================
# CLEAN DATA
# =========================================================

df = df.copy()

df["Time on ice"] = pd.to_numeric(
    df["Time on ice"],
    errors="coerce"
)

df = df.dropna(subset=["Time on ice"])

df = df[df["Time on ice"] > 0]

# =========================================================
# MINIMUM TOI FILTER
# =========================================================

MIN_TOI = 200

df = df[df["Time on ice"] >= MIN_TOI]

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
# NUMERIC CONVERSION
# =========================================================

for metric in metrics:

    df[metric] = pd.to_numeric(
        df[metric],
        errors="coerce"
    ).fillna(0)

# =========================================================
# PER60
# =========================================================

for metric in metrics:

    df[f"{metric}_per60"] = (
        df[metric] / df["Time on ice"]
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
# ATTRIBUTE GRADES
# =========================================================

df["Scoring"] = (
    (
        df["Goals_per60"].rank(pct=True)
        +
        df["xG_per60"].rank(pct=True)
        +
        df["Shots_per60"].rank(pct=True)
    ) / 3
) * 6 + 4

df["Playmaking"] = (
    (
        df["First assist_per60"].rank(pct=True)
        +
        df["Passes to the slot_per60"].rank(pct=True)
    ) / 2
) * 6 + 4

df["Transition"] = (
    df["Entries_per60"].rank(pct=True)
) * 6 + 4

df["Defense"] = (
    (
        df["Takeaways_per60"].rank(pct=True)
        +
        (
            1 -
            df["Opponent's xG when on ice_per60"]
            .rank(pct=True)
        )
    ) / 2
) * 6 + 4

df["Puck Management"] = (
    (
        1 -
        df["Puck losses_per60"].rank(pct=True)
    )
) * 6 + 4

# =========================================================
# ROUND ATTRIBUTE GRADES
# =========================================================

attribute_cols = [
    "Scoring",
    "Playmaking",
    "Transition",
    "Defense",
    "Puck Management"
]

for col in attribute_cols:

    df[col] = df[col].round(1)

# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("Filters")

# Team
teams = sorted(df["Team"].dropna().unique())

selected_team = st.sidebar.selectbox(
    "Team",
    ["All Teams"] + teams
)

# Position
positions = sorted(df["Position"].dropna().unique())

selected_position = st.sidebar.selectbox(
    "Position",
    ["All Positions"] + positions
)

# =========================================================
# APPLY FILTERS
# =========================================================

filtered_df = df.copy()

if selected_team != "All Teams":

    filtered_df = filtered_df[
        filtered_df["Team"] == selected_team
    ]

if selected_position != "All Positions":

    filtered_df = filtered_df[
        filtered_df["Position"] == selected_position
    ]

# =========================================================
# PLAYER SELECTORS
# =========================================================

players = sorted(filtered_df["Player"].unique())

player1 = st.selectbox(
    "Player 1",
    players,
    index=0
)

player2 = st.selectbox(
    "Player 2",
    players,
    index=min(1, len(players)-1)
)

p1 = filtered_df[
    filtered_df["Player"] == player1
].iloc[0]

p2 = filtered_df[
    filtered_df["Player"] == player2
].iloc[0]

# =========================================================
# PLAYER OVERVIEW
# =========================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader(player1)

    st.metric(
        "Grade",
        p1["Grade"]
    )

    st.metric(
        "Projection Score",
        round(
            p1["Projection Score"],
            2
        )
    )

with col2:

    st.subheader(player2)

    st.metric(
        "Grade",
        p2["Grade"]
    )

    st.metric(
        "Projection Score",
        round(
            p2["Projection Score"],
            2
        )
    )

# =========================================================
# SPIDER CHART
# =========================================================

categories = [
    "Scoring",
    "Playmaking",
    "Transition",
    "Defense",
    "Puck Management"
]

fig = go.Figure()

fig.add_trace(go.Scatterpolar(

    r=[
        p1[c] for c in categories
    ],

    theta=categories,

    fill='toself',

    name=player1
))

fig.add_trace(go.Scatterpolar(

    r=[
        p2[c] for c in categories
    ],

    theta=categories,

    fill='toself',

    name=player2
))

fig.update_layout(

    polar=dict(

        radialaxis=dict(
            visible=True,
            range=[4, 10]
        )
    ),

    showlegend=True,

    height=700
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =========================================================
# PLAYER DATA TABLE
# =========================================================

st.subheader("Player Comparison")

comparison_df = pd.DataFrame({

    "Attribute": categories,

    player1: [
        p1[c] for c in categories
    ],

    player2: [
        p2[c] for c in categories
    ]
})

st.dataframe(
    comparison_df,
    use_container_width=True
)
