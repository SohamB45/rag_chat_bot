import os
from sentence_transformers import SentenceTransformer

# Set cache directory
cache_dir = "./models"
os.makedirs(cache_dir, exist_ok=True)

print("📥 Downloading embedding model...")
model = SentenceTransformer(
    'sentence-transformers/all-MiniLM-L6-v2',
    cache_folder=cache_dir
)
print(f"✅ Model downloaded to {cache_dir}")
