from sentence_transformers import SentenceTransformer

# Pre-download the model
print("📥 Downloading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print("✅ Model downloaded successfully!")
