"""
ui.py — shared visual layer: fonts, CSS injection, and small HTML components
(hero banner, page header, stat tiles, section titles) used on every page so
the app reads as one designed product instead of default Streamlit widgets
bolted together.

Kept theme-safe deliberately: nothing here hardcodes a light-only text color
over an inherited background. The hero banner is the one exception — its
background is a fixed gradient, so white text on it is always correct
regardless of the viewer's light/dark setting.
"""
import streamlit as st

from theme import CATEGORICAL

_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&family=Manrope:wght@700;800&display=swap"
)


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('{_FONTS}');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, "Segoe UI", sans-serif;
        }}

        .block-container {{
            padding-top: 2.2rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }}

        /* ---- hero banner (home page only) ---- */
        .cri-hero {{
            background: linear-gradient(135deg, #0d366b 0%, #1c5cab 45%, #2a78d6 100%);
            border-radius: 20px;
            padding: 2.5rem 2.75rem;
            margin-bottom: 1.75rem;
            color: #ffffff;
            box-shadow: 0 20px 45px -22px rgba(13,54,107,0.55);
            position: relative;
            overflow: hidden;
        }}
        .cri-hero::after {{
            content: "";
            position: absolute; inset: 0;
            background: radial-gradient(circle at 88% 15%, rgba(255,255,255,0.16), transparent 55%);
        }}
        .cri-hero h1 {{
            font-family: 'Manrope', 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2.3rem;
            margin: 0 0 .5rem 0;
            letter-spacing: -0.02em;
            position: relative;
            color: #ffffff;
        }}
        .cri-hero p {{
            font-size: 1.02rem;
            opacity: .92;
            margin: 0;
            max-width: 660px;
            position: relative;
            line-height: 1.55;
            color: #ffffff;
        }}
        .cri-badges {{ margin-top: 1.1rem; display: flex; gap: .5rem; flex-wrap: wrap; position: relative; }}
        .cri-badge {{
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.30);
            padding: .3rem .8rem;
            border-radius: 999px;
            font-size: .76rem;
            font-weight: 600;
            letter-spacing: .02em;
            color: #ffffff;
        }}

        /* ---- compact page header (every other page) ---- */
        .cri-page-header {{ display: flex; align-items: center; gap: .7rem; margin-bottom: .1rem; }}
        .cri-page-header .cri-icon {{
            font-size: 1.7rem; line-height: 1;
            width: 46px; height: 46px; border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            background: rgba(42,120,214,0.12);
        }}
        .cri-page-header .cri-title {{
            font-family: 'Manrope', 'Inter', sans-serif;
            font-weight: 800; font-size: 1.55rem; letter-spacing: -0.01em;
        }}

        /* ---- section title rule ---- */
        .cri-section-title {{
            font-family: 'Manrope', 'Inter', sans-serif;
            font-weight: 700; font-size: 1.02rem;
            margin: .2rem 0 .7rem 0;
            padding-bottom: .45rem;
            border-bottom: 2px solid rgba(42,120,214,0.18);
        }}

        /* ---- stat tiles: flex row that WRAPS whole tiles onto a new line
           when narrow, rather than st.columns() squeezing text into a
           mid-number line break inside a fixed-width column. ---- */
        .cri-tile-row {{
            display: flex; flex-wrap: wrap; gap: .9rem; margin-bottom: .25rem;
        }}
        .cri-tile {{
            flex: 1 1 190px; min-width: 168px;
            background: rgba(130,130,130,0.06);
            border: 1px solid rgba(130,130,130,0.16);
            border-top: 3px solid var(--accent, #2a78d6);
            border-radius: 14px;
            padding: .95rem 1.1rem .85rem 1.1rem;
        }}
        .cri-tile .cri-tile-label {{
            text-transform: uppercase; letter-spacing: .06em;
            font-size: .66rem; font-weight: 700; color: #898781;
            margin-bottom: .3rem; white-space: nowrap;
        }}
        .cri-tile .cri-tile-value {{
            font-family: 'Manrope', 'Inter', sans-serif;
            font-size: 1.35rem; font-weight: 800; letter-spacing: -0.01em; line-height: 1.15;
            white-space: nowrap;
        }}
        .cri-tile .cri-tile-sub {{ font-size: .74rem; color: #898781; margin-top: .3rem; }}

        /* ---- card-wrapped containers (chart panels) ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            border: 1px solid rgba(130,130,130,0.16) !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 10px 28px -20px rgba(0,0,0,0.5);
        }}

        [data-testid="stSidebar"] {{ border-right: 1px solid rgba(130,130,130,0.14); }}
        [data-testid="stMetricValue"] {{ font-family: 'Manrope', 'Inter', sans-serif; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 1.5rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badges: list[str] | None = None) -> None:
    badges_html = "".join(f'<span class="cri-badge">{b}</span>' for b in (badges or []))
    st.markdown(
        f'<div class="cri-hero"><h1>{title}</h1><p>{subtitle}</p>'
        f'<div class="cri-badges">{badges_html}</div></div>',
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str) -> None:
    st.markdown(
        f'<div class="cri-page-header"><div class="cri-icon">{icon}</div>'
        f'<div class="cri-title">{title}</div></div>',
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="cri-section-title">{title}</div>', unsafe_allow_html=True)


def tile_row(items: list[dict]) -> None:
    """Renders a row of stat tiles as ONE flex-wrap HTML block (not
    st.columns()), so tiles wrap onto a new line on narrow viewports instead
    of squeezing numbers into an ugly mid-value line break inside a rigid
    fixed-width column. Each item: {label, value, sub (optional), accent (optional)}."""
    # NOTE: every card is built as ONE unindented line. st.markdown() treats
    # 4-space-indented lines as a preformatted code block per CommonMark, so
    # a "readable", multi-line, indented f-string here renders as literal
    # escaped HTML text instead of a styled card — this bit once already.
    cards = []
    for it in items:
        accent = it.get("accent", CATEGORICAL[0])
        sub = it.get("sub", "")
        sub_html = f'<div class="cri-tile-sub">{sub}</div>' if sub else ""
        cards.append(
            f'<div class="cri-tile" style="--accent:{accent}">'
            f'<div class="cri-tile-label">{it["label"]}</div>'
            f'<div class="cri-tile-value">{it["value"]}</div>'
            f'{sub_html}</div>'
        )
    st.markdown(f'<div class="cri-tile-row">{"".join(cards)}</div>', unsafe_allow_html=True)
