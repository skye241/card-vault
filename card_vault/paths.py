from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMAGES = DATA / "images"
SAMPLES = DATA / "samples"
API_CACHE = DATA / "api_cache"
CATALOG_PATH = DATA / "catalog.json"
EMBEDDINGS_PATH = DATA / "embeddings.npz"
