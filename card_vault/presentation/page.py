"""Insurance check screen. Upload a slab, then show the quote and price chart."""

import pandas as pd
import streamlit as st

from card_vault.application.eligibility import rejection_reason
from card_vault.application.quote import quote_slab
from card_vault.application.read_slab import read_slab
from card_vault.infrastructure.pokemon_api import price_history

_STYLE = """
<style>
.block-container {padding-top: 2.4rem; padding-bottom: 3rem; max-width: 980px;}
h1 {font-weight: 600; letter-spacing: -0.03em; margin-bottom: 0.2rem;}
.price {
    font-size: 40px;
    font-weight: 600;
    letter-spacing: -0.04em;
    line-height: 1.1;
    color: #0B6E4F;
    margin: 0.15rem 0 0;
}
.source {
    margin: 0.2rem 0 0.6rem;
    color: #6d675e;
    font-size: 0.95rem;
}
div[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
div[data-testid="stFileUploaderDropzone"] {min-height: 220px;}
div[data-testid="stVerticalBlockBorderWrapper"] {min-height: 220px;}
</style>
"""


def main() -> None:
    """Render the valuation page. Streamlit reruns this on each interaction."""
    st.set_page_config(page_title="Graded card valuation", layout="wide")
    st.markdown(_STYLE, unsafe_allow_html=True)
    st.title("Pókemon Graded card valuation")
    st.caption("Upload a straight-on photo of a Pokémon slab.")
    st.caption("Supported card grading companies: PSA, SGC, CGC, ACE, Beckett/BGS, and TAG.")

    photo_column, result_column = st.columns([1, 1.1], gap="large")
    with photo_column:
        uploaded = st.file_uploader(
            "Slab photo",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.image(uploaded, width="stretch")

    with result_column:
        if uploaded is None:
            with st.container(border=True):
                st.markdown("**Waiting for a slab**")
            return
        with st.spinner("Reading the slab"):
            slab = read_slab(uploaded.getvalue())
        reason = rejection_reason(slab)
        if reason:
            st.error(reason)
            return
        _show_quote(slab)


def _show_quote(slab) -> None:
    st.success("Congratulations, your graded card is verified. Check out your card valuation below.")
    st.subheader(slab.card_name or "Graded card")
    try:
        quote = quote_slab(slab)
    except Exception as error:
        st.warning(str(error))
    else:
        st.html(
            f'<p class="price">{quote.symbol}{quote.amount:,.2f}</p>'
            f'<p class="source">Source: {quote.source}</p>'
        )
        if quote.card_id is not None:
            _show_price_chart(quote.card_id)
    company, grade = st.columns(2)
    company.metric("Company", slab.company or "—")
    grade.metric("Grade", slab.grade or "—")
    year, cert = st.columns(2)
    year.metric("Year", slab.year or "—")
    cert.metric("Cert", slab.cert_number or "—")


def _show_price_chart(card_id: int) -> None:
    try:
        with st.spinner("Loading price history"):
            history = price_history(card_id)
    except Exception as error:
        st.caption(f"Price history unavailable: {error}")
        return
    columns = [
        name for name in ("Cardmarket", "TCGPlayer")
        if any(row.get(name) is not None for row in history.rows)
    ]
    if not columns:
        st.caption("No price history for this card.")
        return
    st.line_chart(pd.DataFrame(history.rows), x="date", y=columns, x_label="Date", y_label="Price")
    st.caption(history.note)
