import streamlit as st

from functions.extractor import extract_slab_info
from functions.valuation import get_market_value

st.set_page_config(page_title="Graded card valuation", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2.4rem; padding-bottom: 3rem; max-width: 980px;}
    h1 {font-weight: 600; letter-spacing: -0.03em; margin-bottom: 0.2rem;}
    .eyebrow {
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-size: 0.75rem;
        color: #6d675e;
        margin-bottom: 0.35rem;
    }
    .price {
        font-size: 2.75rem;
        font-weight: 600;
        letter-spacing: -0.04em;
        line-height: 1.1;
        color: #0B6E4F;
        margin: 0.15rem 0 0.25rem;
    }
    div[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
    div[data-testid="stFileUploaderDropzone"] {min-height: 220px;}
    div[data-testid="stVerticalBlockBorderWrapper"] {min-height: 220px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="eyebrow">Insurance check</p>', unsafe_allow_html=True)
st.title("Graded card valuation")
st.caption("Upload a straight-on photo of the slab. A raw card cannot be quoted.")

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
    else:
        with st.spinner("Reading the slab"):
            slab_info = extract_slab_info(uploaded.getvalue())
        if not slab_info.is_graded:
            st.error("Ineligible for Insurance (Ungraded Card)")
        else:
            st.success("Congratulations, your graded card is verified. Check out your card valuation below.")
            st.subheader(slab_info.card_name or "Graded card")
            try:
                price = get_market_value(slab_info)
            except Exception as error:
                st.warning(str(error))
            else:
                st.markdown("Covered Value")
                st.markdown(f'<h4 class="price">${price:,.2f}</h4>', unsafe_allow_html=True)
                st.caption("Source: eBay median listing prices")
            company, grade, year, cert = st.columns(4)
            company.metric("Company", slab_info.company or "—")
            grade.metric("Grade", slab_info.grade or "—")
            year.metric("Year", slab_info.year or "—")
            cert.metric("Cert", slab_info.cert_number or "—")
