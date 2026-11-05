"""Card Vault: photo in, resale quote out."""

from __future__ import annotations

import streamlit as st
from PIL import Image

from card_vault.build import build_vault
from card_vault.catalog import load_catalog, refresh_prices
from card_vault.identify import Identifier, match_label
from card_vault.paths import DATA
from card_vault.pricing import CONDITIONS, DEFAULT_CONDITION, VARIANT_LABELS, money, quote
from card_vault.samples import load_rgb

st.set_page_config(page_title="Card Vault", page_icon="◆", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1080px;}
    h1 {font-weight: 650; letter-spacing: -0.03em; margin-bottom: 0.2rem;}
    div[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_identifier(built_at: str) -> Identifier:
    catalog = load_catalog()
    if catalog is None:
        raise RuntimeError("Reference vault is missing.")
    return Identifier.load(catalog)


def live_candidates(candidates: list[dict], catalog: dict) -> list[dict]:
    by_id = {card["id"]: card for card in catalog["cards"]}
    hydrated = []
    for hit in candidates:
        card = by_id.get(hit["id"])
        if not card:
            continue
        merged = dict(hit)
        for key in ("market", "low", "mid", "price_variant", "price_updated_at", "tcgplayer_url", "image"):
            merged[key] = card.get(key)
        hydrated.append(merged)
    return hydrated


def add_to_vault(token: str, preview: bytes, image: Image.Image, identifier: Identifier, catalog: dict) -> None:
    vault = st.session_state.vault
    if any(item["token"] == token for item in vault):
        st.toast("Already in the vault")
        return
    hits = live_candidates(identifier.search(image), catalog)
    if not hits:
        st.error("No reference card was close enough to price this photo.")
        return
    vault.append({"token": token, "preview": preview, "candidates": hits})


def render_vault(catalog: dict) -> None:
    vault = st.session_state.vault
    rows = []
    for item in vault:
        candidates = live_candidates(item["candidates"], catalog)
        if not candidates:
            continue
        pick = int(st.session_state.get(f"pick-{item['token']}", 0))
        pick = min(pick, len(candidates) - 1)
        condition = st.session_state.get(f"cond-{item['token']}", DEFAULT_CONDITION)
        card = candidates[pick]
        rows.append((card, quote(card["market"], condition), match_label(card["score"], card["margin"], pick != 0)))

    uncertain = sum(1 for _, _, label in rows if label == "Uncertain match")
    total = sum(amount for _, amount, _ in rows)
    metric_cards, metric_total, metric_uncertain = st.columns(3)
    metric_cards.metric("Cards in vault", len(rows))
    metric_total.metric("Resale quote", money(total), help="US dollars. TCGPlayer resale value, not your purchase price.")
    metric_uncertain.metric("Uncertain matches", uncertain)

    if uncertain:
        st.warning("Confirm each uncertain card before you rely on the total.")

    for item in vault:
        candidates = live_candidates(item["candidates"], catalog)
        if not candidates:
            continue
        token = item["token"]
        pick = min(int(st.session_state.get(f"pick-{token}", 0)), len(candidates) - 1)
        card = candidates[pick]
        label = match_label(card["score"], candidates[0]["margin"] if pick == 0 else card["margin"], pick != 0)
        amount = quote(card["market"], st.session_state.get(f"cond-{token}", DEFAULT_CONDITION))

        with st.container(border=True):
            photo_col, official_col, detail_col = st.columns([1, 1, 1.5])
            photo_col.image(item["preview"], caption="Your photo", width="stretch")
            official_path = DATA / card["image"] if card.get("image") else None
            if official_path and official_path.exists():
                official_col.image(str(official_path), caption="Matched printing", width="stretch")
            with detail_col:
                st.subheader(f"{card['name']}")
                st.caption(f"{card['set_name']} · #{card['number']} · {card.get('rarity') or 'Pokémon'}")
                if label == "Uncertain match":
                    st.warning(label)
                else:
                    st.success(label)
                runner_up = candidates[1] if len(candidates) > 1 else None
                similarity = f"Visual similarity {card['score']:.0%}"
                if runner_up and pick == 0:
                    similarity += f" · next is {runner_up['name']} at {runner_up['score']:.0%}"
                st.caption(similarity)

                if len(candidates) > 1:
                    st.radio(
                        "Quoted card",
                        list(range(len(candidates))),
                        format_func=lambda index, options=candidates: (
                            f"{options[index]['name']} · {options[index]['set_name']} #{options[index]['number']}"
                        ),
                        key=f"pick-{token}",
                    )
                condition = st.selectbox(
                    "Condition",
                    list(CONDITIONS),
                    key=f"cond-{token}",
                    help="TCGPlayer's market price is Near Mint. Other conditions apply a resale discount. This does not grade the photo.",
                )
                factor = CONDITIONS[condition]
                st.metric("Quote", money(quote(card["market"], condition)))
                variant = VARIANT_LABELS.get(card["price_variant"], card["price_variant"])
                updated = card.get("price_updated_at") or "unknown date"
                st.caption(
                    f"{money(card['market'])} near-mint {variant} resale × {factor:.0%} · TCGPlayer {updated}"
                )
                if card.get("low") is not None and card.get("mid") is not None:
                    low = money(float(card["low"])).replace("$", r"\$")
                    mid = money(float(card["mid"])).replace("$", r"\$")
                    st.caption(f"Listing range, low to mid: {low} to {mid}")
                if card.get("tcgplayer_url"):
                    st.link_button("View market listings", card["tcgplayer_url"])
                if st.button("Remove", key=f"rm-{token}"):
                    st.session_state.vault = [entry for entry in vault if entry["token"] != token]
                    st.rerun()


def main() -> None:
    if "vault" not in st.session_state:
        st.session_state.vault = []

    st.title("Card Vault")
    st.write(
        "Upload a Pokémon card and get a fast quote based on what it sells for now, not what you paid."
    )

    catalog = load_catalog()
    if catalog is None:
        st.info("The reference vault has not been built on this machine yet.")
        if st.button("Build reference vault", type="primary"):
            with st.spinner("Fetching cards and prices, then building the image index. The first run takes a few minutes."):
                build_vault()
            get_identifier.clear()
            st.rerun()
        return

    dates = sorted(card["price_updated_at"] for card in catalog["cards"] if card.get("price_updated_at"))
    date_line = f"{dates[0]} – {dates[-1]}" if dates else "unavailable"
    st.caption(
        f"{len(catalog['cards'])} higher-value cards in the reference vault. "
        f"TCGPlayer updates: {date_line}. Prices in USD."
    )

    identifier = get_identifier(catalog["built_at"])
    upload_col, sample_col = st.columns([1.2, 1])
    with upload_col:
        uploads = st.file_uploader(
            "Card photos",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            help="One card per photo, front facing, filling the frame.",
        )
    with sample_col:
        st.caption("No cards handy? These are phone-style photos of reference printings.")
        for sample in catalog.get("samples") or []:
            if st.button(sample["label"], key=f"sample-{sample['id']}", width="stretch"):
                path = DATA / sample["file"]
                add_to_vault(f"sample:{sample['id']}", path.read_bytes(), load_rgb(path), identifier, catalog)

    if uploads:
        for uploaded in uploads:
            token = f"upload:{uploaded.name}:{uploaded.size}"
            if any(item["token"] == token for item in st.session_state.vault):
                continue
            preview = uploaded.getvalue()
            uploaded.seek(0)
            image = Image.open(uploaded).convert("RGB")
            add_to_vault(token, preview, image, identifier, catalog)

    st.divider()
    if not st.session_state.vault:
        st.write("Your vault is empty. Add a photo to see a resale quote.")
    else:
        render_vault(catalog)

    with st.expander("How this quote is made"):
        st.write(
            "Card Vault compares your photo with official art for higher-value Pokémon cards, "
            "using CLIP embeddings and cosine similarity. TCGPlayer’s market price is the near-mint resale price. "
            "You confirm the printing and the condition. Lightly Played, Moderately Played, and Heavily Played "
            "are 85%, 70%, and 50% of that price."
        )
        st.write(
            "This does not grade the card from the photo, does not call eBay, and is not an insurance policy. "
            "A weak match stays in the total only so you can correct it."
        )
        refresh_col, rebuild_col = st.columns(2)
        if refresh_col.button("Refresh resale prices"):
            with st.spinner("Updating TCGPlayer prices…"):
                refresh_prices(catalog)
            st.rerun()
        if rebuild_col.button("Rebuild reference vault"):
            with st.spinner("Rebuilding the vault…"):
                build_vault()
            get_identifier.clear()
            st.rerun()


main()
