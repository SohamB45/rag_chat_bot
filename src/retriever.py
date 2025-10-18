# # src/retriever.py
# import os
# from threading import Lock
# from dotenv import load_dotenv

# load_dotenv()

# # Use absolute paths so Render finds indices/models reliably
# REPO_ROOT = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# CHROMA_DIR = os.environ.get("INDICES_DIR", os.path.join(REPO_ROOT, "indices"))
# CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", os.path.join(REPO_ROOT, "models"))

# # Lazy singletons
# _retriever = None
# _load_lock = Lock()

# def load_retriever(k=3):
#     """
#     Load (or return cached) LangChain Chroma retriever.
#     Returns: retriever
#     """
#     global _retriever
#     if _retriever is not None:
#         return _retriever

#     with _load_lock:
#         if _retriever is not None:
#             return _retriever

#         if not os.path.exists(CHROMA_DIR):
#             raise FileNotFoundError(
#                 f"No vector database found at {CHROMA_DIR}. Please run ingest.py first."
#             )

#         # Import inside function so module import doesn't fail when packages missing in some environments
#         from langchain_community.embeddings import HuggingFaceEmbeddings
#         from langchain_community.vectorstores import Chroma

#         print(f"🔹 Loading Chroma DB from: {CHROMA_DIR}")
#         print(f"🔹 Using HF cache folder: {CACHE_DIR}")

#         embeddings = HuggingFaceEmbeddings(
#             model_name="sentence-transformers/all-MiniLM-L6-v2",
#             cache_folder=CACHE_DIR
#         )

#         vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
#         retriever = vectordb.as_retriever(search_kwargs={"k": k})

#         _retriever = retriever
#         print("✅ Chroma retriever loaded and cached.")
#         return _retriever

# def retrieve_documents(query, k=3):
#     """
#     Convenience wrapper for retrieving documents.
#     Returns a list of Document-like objects with `.page_content` and `.metadata`.
#     """
#     r = load_retriever(k=k)
#     results = r.get_relevant_documents(query)
#     # Convert to simple dicts for downstream code
#     docs = []
#     for d in results:
#         # langchain Document has .page_content and .metadata
#         docs.append({"text": getattr(d, "page_content", str(d)), "metadata": getattr(d, "metadata", {})})
#     return docs

# # --------------------------------------------
# # Backwards-compatible aliases
# # --------------------------------------------

# def get_retriever(k=3):
#     """Alias for load_retriever (for older imports)."""
#     return load_retriever(k=k)


# # def get_relevant_documents(query, k=3):
# #     """Convenience wrapper for retrieving relevant documents directly."""
#     r = load_retriever(k=k)
#     return r.get_relevant_documents(query)



# src/retriever.py
import os
from threading import Lock
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

REPO_ROOT = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.environ.get("INDICES_DIR", os.path.join(REPO_ROOT, "indices"))
CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", os.path.join(REPO_ROOT, "models"))

# singletons
_client = None
_collection = None
_embedding_model = None
_lock = Lock()

def _init_chroma():
    global _client, _collection
    if _client is not None and _collection is not None:
        return
    # persistent client points at directory where Chroma persisted data exists
    _client = chromadb.PersistentClient(path=CHROMA_DIR)
    # adjust collection name to what you used in ingest.py
    _collection = _client.get_or_create_collection("faq_data")
    return

def load_retriever(k=3):
    """
    Loads (and caches) sentence-transformer model + chroma collection.
    Returns a lightweight object with `get_relevant_documents(query)` method.
    """
    global _embedding_model
    with _lock:
        if _collection is None:
            if not os.path.exists(CHROMA_DIR):
                raise FileNotFoundError(f"No vector database found at {CHROMA_DIR}. Please run ingest.py first.")
            _init_chroma()

        if _embedding_model is None:
            # Load the small sentence-transformers model from the cache folder (downloaded by download.py)
            _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder=CACHE_DIR)

    class Retriever:
        def __init__(self, collection, embed_model, k):
            self.collection = collection
            self.embed_model = embed_model
            self.k = k

        def get_relevant_documents(self, query):
            emb = self.embed_model.encode([query], convert_to_numpy=True, show_progress_bar=False)[0]
            # query Chroma by passing precomputed embedding
            res = self.collection.query(query_embeddings=[emb.tolist()], n_results=self.k)
            docs = []
            for i in range(len(res["documents"][0])):
                docs.append({
                    "page_content": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i]
                })
            return docs

    return Retriever(_collection, _embedding_model, k=k)

# convenience wrappers for backward compatibility
def get_retriever(k=3):
    return load_retriever(k=k)

def get_relevant_documents(query, k=3):
    r = load_retriever(k=k)
    return r.get_relevant_documents(query)


