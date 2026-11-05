"""Make straight-on photos a bit more like a phone picture, without leaving the card frame."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageEnhance

from card_vault.paths import DATA, SAMPLES


def load_rgb(path) -> Image.Image:
    image = Image.open(path)
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        return background
    return image.convert("RGB")


def phone_like(image: Image.Image) -> Image.Image:
    """Brightness, a small rotation, and JPEG compression. The card still fills the frame."""
    image = image.convert("RGB")
    image = ImageEnhance.Brightness(image).enhance(1.07)
    image = ImageEnhance.Contrast(image).enhance(0.94)
    image = image.rotate(2.5, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(28, 28, 28))
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=62)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def write_samples(cards: list[dict]) -> list[dict]:
    by_id = {card["id"]: card for card in cards}
    chosen = [by_id[card_id] for card_id in ("base1-4", "base1-2", "base1-15") if card_id in by_id]
    if len(chosen) < 4:
        for card in sorted(cards, key=lambda item: item["market"], reverse=True):
            if card not in chosen:
                chosen.append(card)
            if len(chosen) == 4:
                break
    SAMPLES.mkdir(parents=True, exist_ok=True)
    for stale in SAMPLES.glob("*"):
        stale.unlink()
    manifest = []
    for card in chosen[:4]:
        source = load_rgb(DATA / card["image"])
        photo = phone_like(source)
        filename = f"{card['id']}.jpg"
        photo.save(SAMPLES / filename, format="JPEG", quality=62)
        manifest.append(
            {
                "id": card["id"],
                "file": f"samples/{filename}",
                "label": f"{card['name']} · {card['set_name']}",
            }
        )
    return manifest
