"""
theme.py — shared color palette and Plotly styling for the app.

All hex values are taken as-is from the project's validated dataviz palette
(categorical, sequential, and status ramps chosen for colorblind-safe
adjacent contrast). Nothing here is eyeballed — see the README's Tech Stack
note on chart styling for where these numbers come from.
"""
import plotly.graph_objects as go
import plotly.io as pio

# ---- Fixed-order categorical (8 hues) — use for a handful of true, unordered
# identities (e.g. Q4 vs Non-Q4). Assign in this order, never reordered per-chart.
CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
               "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

# ---- Sequential single-hue ramp (blue, light -> dark) — use for magnitude
# (heatmap cells, continuous color scales).
SEQUENTIAL_BLUE = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
                    "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab",
                    "#184f95", "#104281", "#0d366b"]

# ---- Ordinal 10-step ramp (blue) — RFM segments have a real rank (best to
# worst by value), so they get ONE hue with monotone lightness steps rather
# than 10 unrelated categorical colors. Darkest = highest value.
RFM_SEGMENT_ORDER = [
    "Champion", "At Risk", "Loyal Customer", "Needs Attention",
    "Potential Loyalist", "New Customer", "Promising", "About to Sleep",
    "Hibernating", "Lost",
]
_ordinal_10 = ["#0d366b", "#104281", "#184f95", "#1c5cab", "#256abf",
               "#2a78d6", "#3987e5", "#5598e7", "#6da7ec", "#86b6ef"]
SEGMENT_COLORS = dict(zip(RFM_SEGMENT_ORDER, _ordinal_10))

# ---- Status palette (fixed, reserved meaning — never used for "series N")
STATUS = {"good": "#0ca30c", "warning": "#fab219",
          "serious": "#ec835a", "critical": "#d03b3b"}

# ---- Chart chrome
GRIDLINE = "#e1e0d9"
MUTED = "#898781"
TEXT_SECONDARY = "#52514e"


def style(fig: go.Figure, *, height: int = 420, legend: bool = False) -> go.Figure:
    """Applies shared, recessive chart chrome: transparent surface (inherits
    Streamlit's own light/dark background), thin gridlines, muted axis text,
    no dual axes. Call last, right before st.plotly_chart()."""
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_SECONDARY, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        if legend else dict(visible=False),
        hovermode="x unified",
    )
    # automargin only on y: numeric/date x-axes never need it and, on a
    # horizontal-bar chart, enabling it on x triggers unwanted tick rotation.
    fig.update_xaxes(showgrid=False, linecolor=GRIDLINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRIDLINE, zeroline=False,
                      tickfont=dict(color=MUTED), automargin=True)
    return fig


pio.templates.default = "plotly_white"
