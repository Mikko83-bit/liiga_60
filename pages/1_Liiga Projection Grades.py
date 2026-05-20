# =========================================================
# SPIDER CHART
# =========================================================

spider_metrics = [
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

fig = go.Figure()

# PLAYER 1
fig.add_trace(go.Scatterpolar(

    r=[
        p1[f"{m}_pct"]
        for m in spider_metrics
    ],

    theta=spider_metrics,

    fill='toself',

    name=player1,

    line=dict(
        color="#00E5FF",
        width=3
    ),

    fillcolor="rgba(0,229,255,0.30)"
))

# PLAYER 2
fig.add_trace(go.Scatterpolar(

    r=[
        p2[f"{m}_pct"]
        for m in spider_metrics
    ],

    theta=spider_metrics,

    fill='toself',

    name=player2,

    line=dict(
        color="#FF4B4B",
        width=3
    ),

    fillcolor="rgba(255,75,75,0.30)"
))

fig.update_layout(

    polar=dict(

        bgcolor="rgba(0,0,0,0)",

        radialaxis=dict(

            visible=True,

            range=[0, 100],

            tickfont=dict(
                size=10
            ),

            gridcolor="rgba(255,255,255,0.15)",

            linecolor="rgba(255,255,255,0.15)"
        ),

        angularaxis=dict(

            tickfont=dict(
                size=11
            ),

            gridcolor="rgba(255,255,255,0.10)",

            linecolor="rgba(255,255,255,0.10)"
        )
    ),

    showlegend=True,

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="center",
        x=0.5
    ),

    height=450,

    margin=dict(
        l=40,
        r=40,
        t=40,
        b=40
    ),

    paper_bgcolor="rgba(0,0,0,0)",

    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
