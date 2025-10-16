


# import os
# import logging
# from retriever import load_retriever, retrieve_documents

# _logger = logging.getLogger(__name__)

# # Optionally preload retriever at import time (safe because load_retriever is idempotent)
# def preload(k=3):
#     try:
#         load_retriever(k=k)
#     except Exception as e:
#         _logger.warning("Preload retriever failed: %s", e)

# # Call once on import to warm up (you can also call from app.startup)
# preload()

# def generate_answer(question, user_type="Windows", top_k=3):
#     """
#     Returns: {"answer": "<text>", "sources": [ {text, metadata}, ... ]}
#     Uses the Chroma retriever to fetch top docs and composes a simple answer.
#     You can replace the composition step with an LLM call if desired.
#     """
#     try:
#         docs = retrieve_documents(question, k=top_k)
#     except FileNotFoundError as e:
#         # No indices found
#         return {"answer": "Knowledge base not found. Please run ingest to create indices.", "sources": []}
#     except Exception as e:
#         _logger.exception("Retrieval failed")
#         return {"answer": f"Retrieval error: {e}", "sources": []}

#     if not docs:
#         return {"answer": "I couldn't find an answer in the knowledge base.", "sources": []}

#     # Simple composition: join top docs (you can do smarter summarization with an LLM)
#     answer_text = "\n\n".join([d["text"] for d in docs])
#     return {"answer": answer_text, "sources": docs}

# src/generator.py
import os
import textwrap
import re
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ------------------------------
# Config from env
# ------------------------------
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
TOP_K = int(os.getenv("RAG_TOP_K", "3"))
MAX_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
TEMPERATURE = float(os.getenv("GEN_TEMPERATURE", "0.0"))

if not COHERE_API_KEY:
    logger.error("COHERE_API_KEY not set in environment")
    # we'll still let module import succeed; calls will error with helpful message

# import Cohere ClientV2 lazily to avoid hard crash on import when env missing
try:
    import cohere
    co = cohere.ClientV2(api_key=COHERE_API_KEY) if COHERE_API_KEY else None
except Exception as e:
    co = None
    logger.warning("Cohere client not available: %s", e)

# Import retriever safely (support both src.* and top-level imports)
try:
    from src.retriever import get_retriever
except Exception:
    try:
        from retriever import get_retriever
    except Exception as e:
        get_retriever = None
        logger.warning("get_retriever import failed: %s", e)

# ------------------------------
# Utility helpers (copied/adapted)
# ------------------------------
def build_context_snippet(docs, max_chars_per_doc: int = 1000):
    parts = []
    for i, d in enumerate(docs, start=1):
        # Support LangChain Document or dict-like
        content = getattr(d, "page_content", None) or (d.get("page_content") if isinstance(d, dict) else str(d))
        snippet = content.strip()
        if len(snippet) > max_chars_per_doc:
            snippet = snippet[:max_chars_per_doc] + " ..."
        parts.append(f"[SOURCE {i}]\n{snippet}")
    return "\n\n".join(parts)

_token_pattern = re.compile(r"\w{3,}")

def simple_token_set(text: str):
    tokens = _token_pattern.findall((text or "").lower())
    return set(tokens)

def is_context_relevant(question: str, context_text: str, threshold: float = 0.12) -> bool:
    q_tokens = simple_token_set(question)
    c_tokens = simple_token_set(context_text)
    if not q_tokens or not c_tokens:
        return False
    overlap = q_tokens.intersection(c_tokens)
    ratio = len(overlap) / max(1, len(q_tokens))
    return ratio >= threshold

# ------------------------------
# Cohere wrapper
# ------------------------------
def call_cohere_chat(prompt_text: str):
    """
    Calls Cohere Chat (ClientV2). Returns string or error message.
    """
    if co is None:
        return "[Cohere client not configured — set COHERE_API_KEY in env]"

    # Construct a combined system+user message similar to your local code
    content = (
        "SYSTEM: You are a helpful assistant. Use the context to answer concisely. "
        "Ask clarifying questions if needed.\n\n"
        f"USER: {prompt_text}"
    )
    messages = [{"role": "user", "content": content}]

    try:
        response = co.chat(
            model="command-a-03-2025",
            messages=messages,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        )
        # Cohere v2 chat returns nested structure; this matches your local usage
        return response.message.content[0].text.strip()
    except Exception as e:
        logger.exception("Cohere API error")
        return f"[Error calling Cohere API: {e}]"

# ------------------------------
# Doc user_type helper
# ------------------------------
def _doc_user_type(doc):
    meta = getattr(doc, "metadata", None)
    if isinstance(meta, dict) and "user_type" in meta:
        return meta.get("user_type")
    if isinstance(doc, dict):
        md = doc.get("metadata") or doc.get("meta") or doc.get("meta_data")
        if isinstance(md, dict) and "user_type" in md:
            return md.get("user_type")
    return None

# ------------------------------
# Main generate_answer function
# ------------------------------
def generate_answer(question: str, top_k: int = TOP_K, user_type: str = "general"):
    """
    Main RAG generation entrypoint.

    Returns:
        dict with keys:
            - "answer": str
            - "source_documents": list (documents used)
    """
    if get_retriever is None:
        return {"answer": "Retriever not configured. Ensure retriever.get_retriever is available.", "source_documents": []}

    try:
        retriever = get_retriever()
    except FileNotFoundError as e:
        # indices missing
        logger.error("Retriever indices missing: %s", e)
        return {"answer": "Knowledge base not found. Please run ingest to create the indices.", "source_documents": []}
    except Exception as e:
        logger.exception("Failed to initialize retriever")
        return {"answer": f"Retriever initialization error: {e}", "source_documents": []}

    # Get candidate docs (we request a bit more then filter)
    try:
        docs = retriever.get_relevant_documents(question)
    except Exception as e:
        logger.exception("Retrieval error")
        return {"answer": f"Retrieval error: {e}", "source_documents": []}

    if not docs:
        return {"answer": "I couldn't find any relevant documents.", "source_documents": []}

    # Filter by user_type if any docs have metadata for it
    matching = [d for d in docs if (_doc_user_type(d) or "").lower() == (user_type or "").lower()]
    selected_docs = matching[:top_k] if matching else docs[:top_k]

    context_text = build_context_snippet(selected_docs)

    # If context seems weak, ask a short clarifying question
    if not is_context_relevant(question, context_text):
        clarifying_prompt = (
            f"The context may be insufficient.\n\nCONTEXT:\n{context_text}\n\nQUESTION:\n{question}\n"
            "Ask one short clarifying question to the user. Do not answer yet."
        )
        clarifying = call_cohere_chat(clarifying_prompt)
        return {"answer": clarifying, "source_documents": selected_docs}

    # Build the final prompt for Cohere
    prompt = textwrap.dedent(
        f"""
        CONTEXT:
        {context_text}

        QUESTION:
        {question}

        USER TYPE:
        {user_type}

        Instruction: Answer concisely, tailor to the user type, say 'I don't know' if not in context.
        """
    ).strip()

    answer = call_cohere_chat(prompt)
    return {"answer": answer, "source_documents": selected_docs}


