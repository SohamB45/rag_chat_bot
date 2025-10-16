# download.py
import os
from sentence_transformers import SentenceTransformer

REPO_ROOT = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.abspath(__file__)))
cache_dir = os.path.join(REPO_ROOT, "models")
os.makedirs(cache_dir, exist_ok=True)

print("📥 Downloading embedding model to", cache_dir)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder=cache_dir)
print(f"✅ Embedding model downloaded to {cache_dir}")
