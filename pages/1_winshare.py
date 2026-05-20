import pandas as pd

# =========================
# LUE DATA
# =========================

df = pd.read_csv("data.csv")

# =========================
# PER60
# =========================

toi_col = "TOI"

stats = [
    "Goals",
    "First assist",
    "xG",
    "Passes to the slot",
    "Entries",
    "Takeaways",
    "Puck losses",
    "Team xG when on ice",
    "Opponent's xG when on ice"
]

for stat in stats:
    df[f"{stat}_per60"] = (
        df[stat] / df[toi_col]
    ) * 60

# =========================
# LIIGAN KESKIARVOT
# =========================

league_avg = {}

for stat in stats:
    league_avg[stat] = df[f"{stat}_per60"].mean()

# =========================
# DELTA METRICS
# =========================

for stat in stats:
    df[f"d_{stat}"] = (
        df[f"{stat}_per60"]
        - league_avg[stat]
    )

# =========================
# PROJECTION SCORE
# =========================

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

# =========================
# PERCENTILE
# =========================

df["Percentile"] = (
    df["Projection Score"]
    .rank(pct=True)
) * 100

# =========================
# 4-10 GRADE
# =========================

df["Grade"] = (
    4 + (df["Percentile"] / 100) * 6
).round(1)

# =========================
# TULOSTUS
# =========================

print(
    df[
        [
            "Player",
            "Projection Score",
            "Percentile",
            "Grade"
        ]
    ]
    .sort_values(
        by="Grade",
        ascending=False
    )
)
