# src/ingest.py
import os
import json
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document  # ⚠️ Important

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "./data")
CHROMA_DIR = os.getenv("INDICES_DIR", "./indices")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

def load_documents():
    """Loads text, PDF, and JSON files from data directory."""
    docs = []
    files = glob.glob(os.path.join(DATA_DIR, "*"))
    for file in files:
        ext = os.path.splitext(file)[1].lower()
        if ext == ".pdf":
            loader = PyPDFLoader(file)
            docs.extend(loader.load())
        elif ext == ".txt":
            loader = TextLoader(file, encoding="utf-8")
            docs.extend(loader.load())
        elif ext == ".json":
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        # Wrap dict as a Document
                        docs.append(Document(page_content=json.dumps(item)))
                else:
                    docs.append(Document(page_content=json.dumps(data)))
        else:
            print(f"⚠️ Skipping unsupported file: {file}")
    return docs

def create_chroma_index():
    print("📂 Loading documents...")
    docs = load_documents()
    if not docs:
        print("❌ No files found in /data. Please add PDF, TXT, or JSON files first.")
        return

    print(f"✅ Loaded {len(docs)} documents.")

    # Split text into manageable chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"🧩 Split into {len(chunks)} chunks.")

    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Create and persist Chroma vector store
    print("⚙️ Creating Chroma index...")
    vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
    vectordb.persist()

    print(f"✅ Chroma index saved successfully at: {CHROMA_DIR}")

if __name__ == "__main__":
    create_chroma_index()
