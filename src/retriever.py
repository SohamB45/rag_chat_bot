# src/retriever.py
import os
from threading import Lock
from dotenv import load_dotenv

load_dotenv()

# Use absolute paths so Render finds indices/models reliably
REPO_ROOT = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DIR = os.environ.get("INDICES_DIR", os.path.join(REPO_ROOT, "indices"))
CACHE_DIR = os.environ.get("MODEL_CACHE_DIR", os.path.join(REPO_ROOT, "models"))

# Lazy singletons
_retriever = None
_load_lock = Lock()

def load_retriever(k=3):
    """
    Load (or return cached) LangChain Chroma retriever.
    Returns: retriever
    """
    global _retriever
    if _retriever is not None:
        return _retriever

    with _load_lock:
        if _retriever is not None:
            return _retriever

        if not os.path.exists(CHROMA_DIR):
            raise FileNotFoundError(
                f"No vector database found at {CHROMA_DIR}. Please run ingest.py first."
            )

        # Import inside function so module import doesn't fail when packages missing in some environments
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma

        print(f"🔹 Loading Chroma DB from: {CHROMA_DIR}")
        print(f"🔹 Using HF cache folder: {CACHE_DIR}")

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=CACHE_DIR
        )

        vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        retriever = vectordb.as_retriever(search_kwargs={"k": k})

        _retriever = retriever
        print("✅ Chroma retriever loaded and cached.")
        return _retriever

def retrieve_documents(query, k=3):
    """
    Convenience wrapper for retrieving documents.
    Returns a list of Document-like objects with `.page_content` and `.metadata`.
    """
    r = load_retriever(k=k)
    results = r.get_relevant_documents(query)
    # Convert to simple dicts for downstream code
    docs = []
    for d in results:
        # langchain Document has .page_content and .metadata
        docs.append({"text": getattr(d, "page_content", str(d)), "metadata": getattr(d, "metadata", {})})
    return docs
