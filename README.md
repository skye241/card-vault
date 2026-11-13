# Graded card valuation

Upload a photo of a graded trading card and get an insurance check: whether the card is in a professional slab, what is printed on that slab, and a current market value.

This is a quote for a policy check. It does not sell insurance.

A raw card is not eligible. The screen then says **Ineligible for Insurance (Ungraded Card)**.

## What a graded photo returns

The model reads the slab and fills in:

| Field | What it is |
| --- | --- |
| Company | PSA, Beckett, CGC, or SGC |
| Grade | The printed grade |
| Card | The card name |
| Year | The four-digit year on the card or slab |
| Cert | The certification number |

The covered value is the median of current eBay asking prices for that year, card, company, and grade. These are live listings, not completed sales. Prices are US dollars.

## How the check works

1. You upload a straight-on photo of the slab (JPEG, PNG, or WebP).
2. GPT-4o mini, called through OpenRouter, reads the image and returns the slab fields as JSON.
3. If the card is ungraded, the check stops.
4. If it is graded, the app searches eBay for `year card company grade` and takes the median listing price.

## Run

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
.venv/bin/streamlit run graded_app.py
```

Put these in `.env`:

| Name | Used for |
| --- | --- |
| `OPENROUTER_API_KEY` | Reading the slab photo |
| `EBAY_CLIENT_ID` | eBay Browse API |
| `EBAY_CLIENT_SECRET` | eBay Browse API |
| `POKEMON_TCG_API_KEY` | Optional. Raises the Pokémon TCG API rate limit |

The eBay credentials are an application keyset. The search uses the production Browse API.
