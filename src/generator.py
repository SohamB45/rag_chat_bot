

# import os
# import textwrap
# import re
# from dotenv import load_dotenv
# from huggingface_hub import InferenceClient

# # ------------------------------
# # Environment setup
# # ------------------------------
# load_dotenv()

# HF_TOKEN = os.getenv("HF_TOKEN")
# HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"  # ✅ stable default model
# TOP_K = int(os.getenv("RAG_TOP_K", "3"))
# MAX_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
# TEMPERATURE = float(os.getenv("GEN_TEMPERATURE", "0.0"))

# if not HF_TOKEN:
#     raise ValueError("HF_TOKEN not set. Add HF_TOKEN=your_token to your .env file.")

# # Import retriever safely
# try:
#     from src.retriever import get_retriever
# except Exception:
#     from retriever import get_retriever


# # ------------------------------
# # Helper functions
# # ------------------------------
# def build_context_snippet(docs, max_chars_per_doc: int = 1000):
#     parts = []
#     for i, d in enumerate(docs, start=1):
#         content = getattr(d, "page_content", None) or (d.get("page_content") if isinstance(d, dict) else str(d))
#         snippet = content.strip()
#         if len(snippet) > max_chars_per_doc:
#             snippet = snippet[:max_chars_per_doc] + " ..."
#         parts.append(f"[SOURCE {i}]\n{snippet}")
#     return "\n\n".join(parts)


# def simple_token_set(text: str):
#     tokens = re.findall(r"\w{3,}", text.lower())
#     return set(tokens)


# def is_context_relevant(question: str, context_text: str, threshold: float = 0.12) -> bool:
#     q_tokens = simple_token_set(question)
#     c_tokens = simple_token_set(context_text)
#     if not q_tokens or not c_tokens:
#         return False
#     overlap = q_tokens.intersection(c_tokens)
#     ratio = len(overlap) / max(1, len(q_tokens))
#     return ratio >= threshold


# # ------------------------------
# # Core HF call (no provider)
# # ------------------------------
# def call_hf_chat(prompt_text: str, system_msg: str = None):
#     """
#     Simple wrapper for Hugging Face free inference (no provider)
#     """
#     client = InferenceClient(api_key=HF_TOKEN)

#     system = {
#         "role": "system",
#         "content": (
#             system_msg
#             if system_msg
#             else (
#                 "You are a helpful, cautious assistant. Use the provided CONTEXT to answer the user's QUESTION. "
#                 "If the context clearly contains the answer, answer concisely and cite sources like [SOURCE 1]. "
#                 "If the context is incomplete or ambiguous, ask a single short clarifying question instead of guessing."
#             )
#         ),
#     }
#     user_msg = {"role": "user", "content": prompt_text}

#     completion = client.chat.completions.create(
#         model=HF_MODEL,
#         messages=[system, user_msg],
#         max_tokens=MAX_TOKENS,
#         temperature=TEMPERATURE,
#     )

#     first_choice = completion.choices[0]
#     msg = first_choice.message
#     content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
#     if isinstance(content, dict) and "parts" in content:
#         return "".join(content["parts"])
#     return content or str(msg)


# # ------------------------------
# # Main RAG logic with user type
# # ------------------------------
# def _doc_user_type(doc):
#     meta = getattr(doc, "metadata", None)
#     if isinstance(meta, dict) and "user_type" in meta:
#         return meta.get("user_type")
#     if isinstance(doc, dict):
#         md = doc.get("metadata") or doc.get("meta") or doc.get("meta_data")
#         if isinstance(md, dict) and "user_type" in md:
#             return md.get("user_type")
#     return None


# def generate_answer(question: str, top_k: int = TOP_K, user_type: str = "general"):
#     retriever = get_retriever()
#     docs = retriever.get_relevant_documents(question)[: top_k * 3]

#     if not docs:
#         return {"answer": "I couldn't find any relevant documents in the knowledge base.", "source_documents": []}

#     matching = [d for d in docs if (_doc_user_type(d) or "").lower() == user_type.lower()]
#     selected_docs = matching[:top_k] if matching else docs[:top_k]

#     context_text = build_context_snippet(selected_docs)

#     if not is_context_relevant(question, context_text, threshold=0.12):
#         clarifying_prompt = (
#             "The provided CONTEXT may not be sufficient to answer the QUESTION.\n\n"
#             f"CONTEXT:\n{context_text}\n\n"
#             f"QUESTION:\n{question.strip()}\n\n"
#             "Please ask one short clarifying question that will help you answer. Do not provide a final answer yet."
#         )
#         clarifying = call_hf_chat(clarifying_prompt)
#         return {"answer": clarifying.strip(), "source_documents": selected_docs}

#     prompt = textwrap.dedent(
#         f"""
#         CONTEXT:
#         {context_text}

#         QUESTION:
#         {question.strip()}

#         USER TYPE:
#         {user_type.strip() if user_type else 'general'}

#         Instruction: Tailor your answer for the given USER TYPE.
#         Use simple, direct language and give relevant examples if possible.
#         Answer concisely and cite sources like [SOURCE 1] where applicable.
#         If not in context, say you don't know.
#         """
#     ).strip()

#     answer = call_hf_chat(prompt)
#     return {"answer": answer, "source_documents": selected_docs}


# # ------------------------------
# # CLI test
# # ------------------------------
# if __name__ == "__main__":
#     print("RAG generator using zephyr-7b-beta (no rate limits)\n")
#     q = input("Question: ").strip()
#     ut = input("User type (e.g., general, admin, beginner): ").strip() or "general"
#     out = generate_answer(q, user_type=ut)
#     print("\n=== Answer ===\n")
#     print(out["answer"])

# import os
# import textwrap
# import re
# from dotenv import load_dotenv
# import cohere

# # ------------------------------
# # Environment setup
# # ------------------------------
# load_dotenv()
# COHERE_API_KEY = os.getenv("COHERE_API_KEY")
# TOP_K = int(os.getenv("RAG_TOP_K", "3"))
# MAX_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "256"))
# TEMPERATURE = float(os.getenv("GEN_TEMPERATURE", "0.0"))

# if not COHERE_API_KEY:
#     raise ValueError("COHERE_API_KEY not set in .env")

# # Cohere ClientV2
# co = cohere.ClientV2(api_key=COHERE_API_KEY)

# # Import retriever safely
# try:
#     from src.retriever import get_retriever
# except Exception:
#     from retriever import get_retriever

# # ------------------------------
# # Helper functions
# # ------------------------------
# def build_context_snippet(docs, max_chars_per_doc: int = 1000):
#     parts = []
#     for i, d in enumerate(docs, start=1):
#         content = getattr(d, "page_content", None) or (d.get("page_content") if isinstance(d, dict) else str(d))
#         snippet = content.strip()
#         if len(snippet) > max_chars_per_doc:
#             snippet = snippet[:max_chars_per_doc] + " ..."
#         parts.append(f"[SOURCE {i}]\n{snippet}")
#     return "\n\n".join(parts)

# def simple_token_set(text: str):
#     tokens = re.findall(r"\w{3,}", text.lower())
#     return set(tokens)

# def is_context_relevant(question: str, context_text: str, threshold: float = 0.12) -> bool:
#     q_tokens = simple_token_set(question)
#     c_tokens = simple_token_set(context_text)
#     if not q_tokens or not c_tokens:
#         return False
#     overlap = q_tokens.intersection(c_tokens)
#     ratio = len(overlap) / max(1, len(q_tokens))
#     return ratio >= threshold

# # ------------------------------
# # Cohere Chat call
# # ------------------------------
# def call_cohere_chat(prompt_text: str):
#     """
#     Cohere ClientV2 chat call. Combine system+user instructions in one string.
#     """
#     # Combine system instructions + user input
#     content = f"""
#         "SYSTEM: You are a helpful assistant. Use the context to answer concisely. "
#         "Ask clarifying questions if needed.\n\n"
#         f"USER: {prompt_text}"
#     """
#     messages = [{"role": "user", "content": content}]

#     try:
#         response = co.chat(
#             model="command-a-03-2025",  # choose appropriate model
#             messages=messages,
#             max_tokens=MAX_TOKENS,
#             temperature=TEMPERATURE
#         )
#         return response.message.content[0].text.strip()
#     except Exception as e:
#         return f"[Error calling Cohere API: {e}]"

# # ------------------------------
# # User type helper
# # ------------------------------
# def _doc_user_type(doc):
#     meta = getattr(doc, "metadata", None)
#     if isinstance(meta, dict) and "user_type" in meta:
#         return meta.get("user_type")
#     if isinstance(doc, dict):
#         md = doc.get("metadata") or doc.get("meta") or doc.get("meta_data")
#         if isinstance(md, dict) and "user_type" in md:
#             return md.get("user_type")
#     return None

# # ------------------------------
# # Main RAG logic
# # ------------------------------
# def generate_answer(question: str, top_k: int = TOP_K, user_type: str = "general"):
#     retriever = get_retriever()
#     docs = retriever.get_relevant_documents(question)[: top_k * 3]

#     if not docs:
#         return {"answer": "I couldn't find any relevant documents.", "source_documents": []}

#     # Filter docs by user_type if present
#     matching = [d for d in docs if (_doc_user_type(d) or "").lower() == user_type.lower()]
#     selected_docs = matching[:top_k] if matching else docs[:top_k]

#     context_text = build_context_snippet(selected_docs)

#     # Ask clarifying question if context seems weak
#     if not is_context_relevant(question, context_text):
#         clarifying_prompt = (
#             f"The context may be insufficient.\n\nCONTEXT:\n{context_text}\n\nQUESTION:\n{question}\n"
#             "Ask one short clarifying question to the user. Do not answer yet."
#         )
#         clarifying = call_cohere_chat(clarifying_prompt)
#         return {"answer": clarifying, "source_documents": selected_docs}

#     # Build final prompt
#     prompt = textwrap.dedent(
#         f"""
#         CONTEXT:
#         {context_text}

#         QUESTION:
#         {question}

#         USER TYPE:
#         {user_type}

#         Instruction: Answer concisely, tailor to the user type,'I don't know' if not in context.
#         """
#     ).strip()

#     answer = call_cohere_chat(prompt)
#     return {"answer": answer, "source_documents": selected_docs}

# # ------------------------------
# # CLI test
# # ------------------------------
# if __name__ == "__main__":
#     q = input("Question: ").strip()
#     ut = input("User type (optional): ").strip() or "general"
#     out = generate_answer(q, user_type=ut)
#     print("\n=== Answer ===\n")
#     print(out["answer"])


# src/generator.py
import os
from threading import Lock
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

_logger = logging.getLogger(__name__)
_embedding_model = None
_load_lock = Lock()

def load_embedding_model(cache_folder=None):
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model
    with _load_lock:
        if _embedding_model is not None:
            return _embedding_model
        repo_root = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.dirname(__file__)))
        cache_folder = cache_folder or os.path.join(repo_root, "models")
        _logger.info(f"Loading embedding model from cache_folder={cache_folder}")
        _embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', cache_folder=cache_folder)
        _logger.info("Embedding model loaded.")
    return _embedding_model

# Example simple generate_answer that uses embeddings + your retriever
def generate_answer(question, user_type="Windows"):
    """
    Should return a dict like {"answer": "...", "sources":[...]}
    Replace the retrieval/generation logic with your app's logic.
    """
    if _embedding_model is None:
        raise RuntimeError("Embedding model not loaded. Call load_embedding_model() at startup.")
    # get embedding for question
    q_emb = _embedding_model.encode([question], convert_to_numpy=True, show_progress_bar=False)[0]
    # TODO: call your retriever to get docs using q_emb
    # For now return a placeholder answer
    answer = f"(demo) Received: {question} (user_type={user_type})"
    return {"answer": answer, "embedding_shape": q_emb.shape}
