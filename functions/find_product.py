from data.schema import TCGProduct

def find_product(card_name: str, products: list[dict]) -> dict:
    print(card_name)
    for prod in products:
        if card_name.lower() in prod["name"].lower():
            return prod
    raise LookupError("No Pokémon cards matches this name")

