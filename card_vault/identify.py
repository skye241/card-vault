"""Match a photo to the reference vault with CLIP embeddings."""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image

from card_vault.paths import DATA, EMBEDDINGS_PATH
from card_vault.samples import load_rgb

MODEL_ID = "openai/clip-vit-base-patch32"
# Artwork window on a straight-on Pokémon card photo, as fractions of the frame.
ART_BOX = (0.10, 0.15, 0.90, 0.50)
ART_WEIGHT = 0.8
TOP_K = 3

# Cosine similarity is not a probability. These gates only decide the label.
STRONG_SCORE = 0.88
STRONG_MARGIN = 0.025
LIKELY_SCORE = 0.80
LIKELY_MARGIN = 0.015


def art_crop(image: Image.Image) -> Image.Image:
    width, height = image.size
    left, top, right, bottom = ART_BOX
    cropped = image.crop(
        (
            int(width * left),
            int(height * top),
            int(width * right),
            int(height * bottom),
        )
    )
    if cropped.size[0] < 8 or cropped.size[1] < 8:
        return image.convert("RGB")
    return cropped


def match_label(score: float, margin: float, overridden: bool) -> str:
    if overridden:
        return "You chose this card"
    if score >= STRONG_SCORE and margin >= STRONG_MARGIN:
        return "Strong match"
    if score >= LIKELY_SCORE and margin >= LIKELY_MARGIN:
        return "Likely match"
    return "Uncertain match"


class Identifier:
    def __init__(self, model, processor, cards: list[dict], art: np.ndarray, full: np.ndarray):
        self.model = model
        self.processor = processor
        self.cards = cards
        self.art = art
        self.full = full

    @classmethod
    def load(cls, catalog: dict) -> "Identifier":
        model, processor = _load_model()
        stored = np.load(EMBEDDINGS_PATH)
        art = stored["art"].astype(np.float32)
        full = stored["full"].astype(np.float32)
        cards = catalog["cards"]
        if art.shape[0] != len(cards) or full.shape[0] != len(cards):
            raise RuntimeError("Embeddings are out of date. Rebuild the reference vault.")
        return cls(model, processor, cards, art, full)

    @classmethod
    def build(cls, cards: list[dict]) -> "Identifier":
        model, processor = _load_model()
        identifier = cls(
            model,
            processor,
            cards,
            np.zeros((0, 1), dtype=np.float32),
            np.zeros((0, 1), dtype=np.float32),
        )
        images = [load_rgb(DATA / card["image"]) for card in cards]
        art, full = identifier._embed_pair(images)
        identifier.art = art
        identifier.full = full
        np.savez(EMBEDDINGS_PATH, art=art, full=full)
        return identifier

    def _embed_images(self, images: list[Image.Image]) -> np.ndarray:
        inputs = self.processor(images=[image.convert("RGB") for image in images], return_tensors="pt")
        with torch.no_grad():
            out = self.model.get_image_features(pixel_values=inputs["pixel_values"])
            # Transformers 5 returns the projected vector on pooler_output.
            if hasattr(out, "pooler_output"):
                embeds = out.pooler_output
            elif torch.is_tensor(out):
                embeds = out
            else:
                embeds = out[-1]
            embeds = embeds / embeds.norm(dim=-1, keepdim=True)
        return embeds.numpy().astype(np.float32)

    def _embed_pair(self, images: list[Image.Image], batch_size: int = 8) -> tuple[np.ndarray, np.ndarray]:
        art_parts = []
        full_parts = []
        for start in range(0, len(images), batch_size):
            batch = images[start : start + batch_size]
            art_parts.append(self._embed_images([art_crop(image) for image in batch]))
            full_parts.append(self._embed_images(batch))
        return np.concatenate(art_parts), np.concatenate(full_parts)

    def search(self, image: Image.Image, k: int = TOP_K) -> list[dict]:
        art, full = self._embed_pair([image.convert("RGB")])
        scores = ART_WEIGHT * (self.art @ art[0]) + (1 - ART_WEIGHT) * (self.full @ full[0])
        order = np.argsort(-scores)
        hits = []
        for rank, index in enumerate(order[:k]):
            score = float(scores[index])
            next_score = float(scores[order[rank + 1]]) if rank + 1 < len(order) else 0.0
            card = self.cards[int(index)]
            hits.append(
                {
                    "id": card["id"],
                    "name": card["name"],
                    "set_name": card["set_name"],
                    "number": card["number"],
                    "rarity": card["rarity"],
                    "image": card["image"],
                    "tcgplayer_url": card.get("tcgplayer_url") or "",
                    "price_updated_at": card.get("price_updated_at") or "",
                    "price_variant": card["price_variant"],
                    "market": card["market"],
                    "low": card.get("low"),
                    "mid": card.get("mid"),
                    "score": score,
                    "margin": score - next_score,
                }
            )
        return hits


_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    from transformers import CLIPModel, CLIPProcessor

    try:
        processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
        model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True)
    except OSError:
        processor = CLIPProcessor.from_pretrained(MODEL_ID)
        model = CLIPModel.from_pretrained(MODEL_ID)
    model.eval()
    _MODEL = (model, processor)
    return _MODEL
