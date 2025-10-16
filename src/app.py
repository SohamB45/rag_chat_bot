
# import os
# import sqlite3
# import streamlit as st
# from datetime import datetime
# from dotenv import load_dotenv

# load_dotenv()

# # Robust imports
# try:
#     from src.generator import generate_answer
#     from src.ingest import create_chroma_index
# except Exception:
#     from generator import generate_answer
#     from ingest import create_chroma_index

# DATA_DIR = os.getenv("DATA_DIR", "./data")
# os.makedirs(DATA_DIR, exist_ok=True)

# # Database setup
# DB_PATH = os.getenv("TICKETS_DB_PATH", "./tickets.db")

# def init_tickets_db():
#     """Initialize the tickets database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS tickets (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user TEXT NOT NULL,
#             platform TEXT NOT NULL,
#             issue TEXT NOT NULL,
#             answer_provided TEXT,
#             timestamp TEXT NOT NULL,
#             status TEXT DEFAULT 'open'
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def save_ticket(user, platform, issue, answer_provided):
#     """Save a ticket to the database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     cursor.execute('''
#         INSERT INTO tickets (user, platform, issue, answer_provided, timestamp)
#         VALUES (?, ?, ?, ?, ?)
#     ''', (user, platform, issue, answer_provided, timestamp))
#     conn.commit()
#     ticket_id = cursor.lastrowid
#     conn.close()
#     return ticket_id

# def get_all_tickets():
#     """Retrieve all tickets from the database"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute('''
#         SELECT id, user, platform, issue, answer_provided, timestamp, status
#         FROM tickets
#         ORDER BY id DESC
#     ''')
#     tickets = cursor.fetchall()
#     conn.close()
#     return tickets

# def get_ticket_count():
#     """Get the count of open tickets"""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
#     count = cursor.fetchone()[0]
#     conn.close()
#     return count

# # Initialize database
# init_tickets_db()

# # Page config
# st.set_page_config(
#     page_title="RAG Chatbot",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Initialize session state FIRST
# if "history" not in st.session_state:
#     st.session_state.history = []

# # Custom CSS for elegant design
# st.markdown("""
#     <style>
#     .main-header {
#         font-size: 2.5rem;
#         font-weight: 600;
#         color: #ffffff;
#         margin-bottom: 0.5rem;
#     }
#     .sub-header {
#         font-size: 1.1rem;
#         color: #6b7280;
#         margin-bottom: 2rem;
#     }
#     .stTextInput > div > div > input {
#         font-size: 1.05rem;
#     }
#     .chat-message {
#         padding: 1.5rem;
#         border-radius: 0.5rem;
#         margin-bottom: 1rem;
#         border-left: 4px solid #3b82f6;
#         background-color: #f9fafb;
#     }
#     .user-badge {
#         display: inline-block;
#         padding: 0.25rem 0.75rem;
#         border-radius: 1rem;
#         background-color: #3b82f6;
#         color: white;
#         font-size: 0.85rem;
#         font-weight: 500;
#         margin-bottom: 0.5rem;
#     }
#     .feedback-section {
#         background-color: #f3f4f6;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin-top: 1rem;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Header
# st.markdown('<div class="main-header"> RAG Customer support Chatbot</div>', unsafe_allow_html=True)


# # Sidebar
# with st.sidebar:
#     st.header("Configuration")
    
#     # User type selection
#     st.subheader("User Type")
#     user_type = st.selectbox(
#         "Select your platform",
#         ["Windows", "Linux", "Zimbra"],
#         index=0,
#         help="Choose your platform for tailored responses"
#     )
    
#     st.divider()
    
#     if st.button("Clear Chat History", use_container_width=True):
#         st.session_state.history = []
#         st.success("Chat history cleared!")
#         st.rerun()
    
#     st.divider()
    
#     # Tickets section
#     st.subheader("Support Tickets")
#     ticket_count = get_ticket_count()
#     if ticket_count > 0:
#         st.metric("Open Tickets", ticket_count)
#         with st.expander("View Tickets"):
#             tickets = get_all_tickets()
#             for ticket in tickets:
#                 ticket_id, user, platform, issue, answer, timestamp, status = ticket
#                 st.markdown(f"**Ticket #{ticket_id}** - `{status}`")
#                 st.text(f"User: {user}")
#                 st.text(f"Platform: {platform}")
#                 st.text(f"Issue: {issue}")
#                 if answer:
#                     with st.expander("View Answer Provided"):
#                         st.text(answer)
#                 st.caption(f"Created: {timestamp}")
#                 if ticket != tickets[-1]:
#                     st.markdown("---")
#     else:
#         st.info("No tickets raised")

# # Initialize session state
# if "history" not in st.session_state:
#     st.session_state.history = []
# if "tickets" not in st.session_state:
#     st.session_state.tickets = []

# # Main chat interface
# st.subheader(" Chat")

# # Query input
# query = st.text_input(
#     "Ask your question",
#     placeholder="Type your question here...",
#     key="query_input",
#     label_visibility="collapsed"
# )

# col1, col2, col3 = st.columns([1, 1, 4])
# with col1:
#     ask = st.button("Ask", use_container_width=True, type="primary")

# # Handle query
# if ask and query:
#     with st.spinner("Searching knowledge base..."):
#         try:
#             out = generate_answer(query, user_type=user_type)
#             answer = out.get("answer", "").strip()
#             st.session_state.history.insert(0, {
#                 "question": query,
#                 "answer": answer,
#                 "user_type": user_type,
#                 "feedback": None,
#                 "ticket_raised": False
#             })
#             st.rerun()
#         except Exception as e:
#             st.error(f"❌ Error: {e}")

# # Display chat history
# st.divider()

# if not st.session_state.history:
#     st.info(" No conversations yet. Ask a question to get started!")
# else:
#     st.subheader("Conversation History")
    
#     for idx, chat in enumerate(st.session_state.history):
#         q = chat["question"]
#         a = chat["answer"]
#         ut = chat["user_type"]
        
#         with st.container():
#             st.markdown(f'<span class="user-badge">{ut}</span>', unsafe_allow_html=True)
#             st.markdown(f"**Q:** {q}")
#             st.markdown(f"**A:** {a}")
            
#             # Feedback section
#             if chat["feedback"] is None and not chat["ticket_raised"]:
#                 st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
#                 st.markdown("**Was this helpful?**")
                
#                 col_yes, col_no, col_space = st.columns([1, 1, 3])
                
#                 with col_yes:
#                     if st.button(" Yes", key=f"helpful_{idx}"):
#                         st.session_state.history[idx]["feedback"] = "helpful"
#                         st.success("Thank you for your feedback!")
#                         st.rerun()
                
#                 with col_no:
#                     if st.button("❌ No, Raise Ticket", key=f"ticket_{idx}"):
#                         # Generate ticket in database
#                         ticket_id = save_ticket(
#                             user="Guest",
#                             platform=ut,
#                             issue=q,
#                             answer_provided=a
#                         )
#                         st.session_state.history[idx]["ticket_raised"] = True
#                         st.success(f"Ticket #{ticket_id} raised successfully!")
#                         st.rerun()
                
#                 st.markdown('</div>', unsafe_allow_html=True)
            
#             elif chat["feedback"] == "helpful":
#                 st.success(" Marked as helpful")
#             elif chat["ticket_raised"]:
#                 st.warning("Support ticket raised for this query")
            
#             if idx < len(st.session_state.history) - 1:
#                 st.divider()



import os
import sqlite3
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Robust imports
try:
    from src.generator import generate_answer, load_embedding_model
    from src.ingest import create_chroma_index
    from src.retriever import load_indices
except Exception:
    from generator import generate_answer, load_embedding_model
    from ingest import create_chroma_index
    from retriever import load_indices

# --------------------------
# Startup: preload models & indices
# --------------------------
REPO_ROOT = os.environ.get("RENDER_REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_CACHE = os.path.join(REPO_ROOT, "models")
INDICES_PATH = os.path.join(REPO_ROOT, "indices")

st.write("⏳ Startup: loading embedding model and indices...")
try:
    load_embedding_model(cache_folder=MODEL_CACHE)
except Exception as e:
    st.error(f"⚠️ Error loading embedding model: {e}")



# --------------------------
# Data directories & DB
# --------------------------
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.getenv("TICKETS_DB_PATH", "./tickets.db")

def init_tickets_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            platform TEXT NOT NULL,
            issue TEXT NOT NULL,
            answer_provided TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'open'
        )
    ''')
    conn.commit()
    conn.close()

def save_ticket(user, platform, issue, answer_provided):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO tickets (user, platform, issue, answer_provided, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user, platform, issue, answer_provided, timestamp))
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()
    return ticket_id

def get_all_tickets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user, platform, issue, answer_provided, timestamp, status
        FROM tickets
        ORDER BY id DESC
    ''')
    tickets = cursor.fetchall()
    conn.close()
    return tickets

def get_ticket_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# Initialize database
init_tickets_db()

# --------------------------
# Streamlit page config
# --------------------------
st.set_page_config(
    page_title="RAG Chatbot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "tickets" not in st.session_state:
    st.session_state.tickets = []

# --------------------------
# Custom CSS
# --------------------------
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 600;
    color: #ffffff;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.1rem;
    color: #6b7280;
    margin-bottom: 2rem;
}
.stTextInput > div > div > input {
    font-size: 1.05rem;
}
.chat-message {
    padding: 1.5rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #3b82f6;
    background-color: #f9fafb;
}
.user-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    background-color: #3b82f6;
    color: white;
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.feedback-section {
    background-color: #f3f4f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"> RAG Customer support Chatbot</div>', unsafe_allow_html=True)

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.header("Configuration")
    
    st.subheader("User Type")
    user_type = st.selectbox(
        "Select your platform",
        ["Windows", "Linux", "Zimbra"],
        index=0,
        help="Choose your platform for tailored responses"
    )
    
    st.divider()
    
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.history = []
        st.success("Chat history cleared!")
        st.rerun()
    
    st.divider()
    
    st.subheader("Support Tickets")
    ticket_count = get_ticket_count()
    if ticket_count > 0:
        st.metric("Open Tickets", ticket_count)
        with st.expander("View Tickets"):
            tickets = get_all_tickets()
            for ticket in tickets:
                ticket_id, user, platform, issue, answer, timestamp, status = ticket
                st.markdown(f"**Ticket #{ticket_id}** - `{status}`")
                st.text(f"User: {user}")
                st.text(f"Platform: {platform}")
                st.text(f"Issue: {issue}")
                if answer:
                    with st.expander("View Answer Provided"):
                        st.text(answer)
                st.caption(f"Created: {timestamp}")
                if ticket != tickets[-1]:
                    st.markdown("---")
    else:
        st.info("No tickets raised")

# --------------------------
# Main Chat Interface
# --------------------------
st.subheader(" Chat")

query = st.text_input(
    "Ask your question",
    placeholder="Type your question here...",
    key="query_input",
    label_visibility="collapsed"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    ask = st.button("Ask", use_container_width=True, type="primary")

if ask and query:
    with st.spinner("Searching knowledge base..."):
        try:
            out = generate_answer(query, user_type=user_type)
            answer = out.get("answer", "").strip()
            st.session_state.history.insert(0, {
                "question": query,
                "answer": answer,
                "user_type": user_type,
                "feedback": None,
                "ticket_raised": False
            })
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {e}")

# --------------------------
# Display chat history
# --------------------------
st.divider()

if not st.session_state.history:
    st.info(" No conversations yet. Ask a question to get started!")
else:
    st.subheader("Conversation History")
    
    for idx, chat in enumerate(st.session_state.history):
        q = chat["question"]
        a = chat["answer"]
        ut = chat["user_type"]
        
        with st.container():
            st.markdown(f'<span class="user-badge">{ut}</span>', unsafe_allow_html=True)
            st.markdown(f"**Q:** {q}")
            st.markdown(f"**A:** {a}")
            
            if chat["feedback"] is None and not chat["ticket_raised"]:
                st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                st.markdown("**Was this helpful?**")
                
                col_yes, col_no, col_space = st.columns([1, 1, 3])
                
                with col_yes:
                    if st.button(" Yes", key=f"helpful_{idx}"):
                        st.session_state.history[idx]["feedback"] = "helpful"
                        st.success("Thank you for your feedback!")
                        st.rerun()
                
                with col_no:
                    if st.button("❌ No, Raise Ticket", key=f"ticket_{idx}"):
                        ticket_id = save_ticket(
                            user="Guest",
                            platform=ut,
                            issue=q,
                            answer_provided=a
                        )
                        st.session_state.history[idx]["ticket_raised"] = True
                        st.success(f"Ticket #{ticket_id} raised successfully!")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            elif chat["feedback"] == "helpful":
                st.success(" Marked as helpful")
            elif chat["ticket_raised"]:
                st.warning("Support ticket raised for this query")
            
            if idx < len(st.session_state.history) - 1:
                st.divider()
