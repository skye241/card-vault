import streamlit as st

from extractor import extract_slab_info
from valuation import get_market_value

st.title("Graded Trading Card Valuation")

uploaded = st.file_uploader("Upload a slab photo", type=["jpg", "jpeg", "png", "webp"])
if uploaded is not None:
    slab_info = extract_slab_info(uploaded.getvalue())
    if not slab_info.is_graded:
        st.error("Ineligible for Insurance (Ungraded Card)")
    else:
        st.success("Graded card — eligible for an insurance check")
        st.table([slab_info.model_dump()])
        st.write(f"Market value: ${get_market_value(slab_info):.2f}")
