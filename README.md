# Graded card valuation

Upload a photo of a graded Pokémon slab and get an insurance check: whether the card can be quoted, the fields printed on the slab, a market value, and a one-year price chart.

This is a quote for a policy check. It does not sell insurance. A raw card is not eligible. A card that is not Pokémon is unsupported for now.

## Layout

The code follows a small clean architecture. Each layer only calls inward.

| Layer | Path | Responsibility |
| --- | --- | --- |
| Domain | `card_vault/domain` | Slab, quote, and price-history models. Set-name matching. Graded price selection. No HTTP and no Streamlit. |
| Application | `card_vault/application` | Read a photo, decide if it can be quoted, and build the quote. |
| Infrastructure | `card_vault/infrastructure` | OpenRouter, the local set catalog, TCGcsv, the Pokémon TCG API, and eBay. |
| Presentation | `card_vault/presentation` | The Streamlit screen. `app.py` is the entry point. |

A quote tries eBay graded prices, then Cardmarket, then TCGPlayer. The slab's grading company is used first. If that company has no grade within 2 points, the fallback order is TAG, ACE, BGS, SGC, CGC, PSA. If nothing graded matches, the quote uses Cardmarket's 7-day average. If the Pokémon card cannot be resolved, the quote is the median of current eBay listings. When the Pokémon card is found, the screen charts the past year of Cardmarket and TCGPlayer prices.

## Run

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

Put these in `.env` or `.streamlit/secrets.toml`:

| Name | Used for |
| --- | --- |
| `OPENROUTER_API_KEY` | Reading the slab photo |
| `POKEMON_TCG_API_KEY` | Pokémon card prices and price history |
| `EBAY_CLIENT_ID` | eBay Browse API, used when the Pokémon lookup fails |
| `EBAY_CLIENT_SECRET` | eBay Browse API |

```bash
.venv/bin/python -m unittest tests.test_quote_rules
```
