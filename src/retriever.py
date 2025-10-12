# src/retriever.py
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

CHROMA_DIR = os.getenv("INDICES_DIR", "./indices")  # You can point to ./data/chroma if you used that earlier

def get_retriever():
    """Load Chroma vector store and return retriever."""
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError(f"No vector database found at {CHROMA_DIR}. Please run ingest.py first.")

    print(f"🔹 Loading Chroma DB from: {CHROMA_DIR}")
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       cache_folder=cache_dir)
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    return retriever

if __name__ == "__main__":
    retriever = get_retriever()
    query = input("Ask a query: ")
    results = retriever.get_relevant_documents(query)
    print("\n🔸 Top Results:")
    for r in results:
        print("-", r.page_content[:200], "\n")
