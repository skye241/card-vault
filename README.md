# Card Vault

Upload a photo of a Pokémon card and get a **resale** quote — the price the card sells for, not the price you paid.

This is the first step of insuring cards you travel with: name the card, confirm its condition, and read a market quote. It does not sell insurance, grade the photo, or call eBay.

## What this tests

A straight-on photo is enough to name a higher-value Pokémon card and attach a current resale price.

## How the quote works

1. A reference vault of higher-value cards is downloaded from the [Pokémon TCG API](https://pokemontcg.io/), including each card’s TCGPlayer **market** price.
2. CLIP embeddings of the artwork and the full card are compared to the photo by cosine similarity.
3. You confirm the card (top three matches) and the condition.
4. Quote = near-mint market price × a condition factor:

| Condition | Factor |
| --- | --- |
| Near Mint | 100% |
| Lightly Played | 85% |
| Moderately Played | 70% |
| Heavily Played | 50% |

Prices are US dollars. The condition factor is an explicit resale discount, not a grade read from the picture.

## Run

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python -m card_vault.build
.venv/bin/streamlit run app.py
```

The first build downloads the CLIP model, card images, and live prices. It takes a few minutes. Later opens reuse `data/`.

Set `POKEMONTCG_API_KEY` if you have one. The app works without it.

In the app, use a sample photo or upload a straight-on front photo that fills the frame (JPEG, PNG, or WebP).
