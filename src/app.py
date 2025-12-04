"""Streamlit web application for Enterprise Document Q&A."""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.generation.rag_chain import EnterpriseRAGChain
from src.utils.logger import setup_logger, get_logger
from src.utils.metrics import get_metrics_collector
from src.config import get_config

# Initialize logger
setup_logger(log_level="INFO", log_file="logs/app.log")
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Enterprise Document Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0078D4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #0078D4;
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state."""
    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "query_count" not in st.session_state:
        st.session_state.query_count = 0
    
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0


def initialize_rag_chain():
    """Initialize the RAG chain."""
    if st.session_state.rag_chain is None:
        try:
            with st.spinner("Initializing system..."):
                config = get_config()
                st.session_state.rag_chain = EnterpriseRAGChain(
                    top_k=st.session_state.get("top_k", 5)
                )
                logger.info("RAG chain initialized successfully")
                return True
        except Exception as e:
            st.error(f"Failed to initialize system: {str(e)}")
            logger.error(f"RAG chain initialization failed: {e}", exc_info=True)
            return False
    return True


def display_header():
    """Display application header."""
    st.markdown('<p class="main-header">📚 Enterprise Document Q&A System</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Powered by Azure AI Foundry, Azure AI Search, and LangChain</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")


def display_sidebar():
    """Display sidebar with settings and statistics."""
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Retrieval settings
        st.subheader("Retrieval Settings")
        top_k = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=5,
            help="More documents provide more context but may increase response time"
        )
        st.session_state.top_k = top_k
        
        min_score = st.slider(
            "Minimum relevance score",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="Filter out documents below this relevance threshold"
        )
        
        # Generation settings
        st.subheader("Generation Settings")
        show_sources = st.checkbox("Show source citations", value=True)
        show_metadata = st.checkbox("Show metadata", value=False)
        
        st.markdown("---")
        
        # Statistics
        st.header("📊 Session Statistics")
        
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_summary()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Queries", summary["total_queries"])
            st.metric("Avg Latency", f"{summary['avg_latency']:.2f}s")
        
        with col2:
            st.metric("Total Tokens", summary["total_tokens"])
            st.metric("Error Rate", f"{summary['error_rate']:.1f}%")
        
        st.markdown("---")
        
        # Actions
        st.header("🔧 Actions")
        
        if st.button("Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.query_count = 0
            st.rerun()
        
        if st.button("Reset Statistics", use_container_width=True):
            metrics_collector.reset()
            st.session_state.total_tokens = 0
            st.rerun()
        
        # Export metrics
        if st.button("Export Metrics", use_container_width=True):
            try:
                filepath = f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                metrics_collector.export_to_json(filepath)
                st.success(f"Metrics exported to {filepath}")
            except Exception as e:
                st.error(f"Export failed: {e}")
        
        st.markdown("---")
        
        # About
        with st.expander("ℹ️ About"):
            st.markdown("""
            **Enterprise Document Q&A System**
            
            This application uses:
            - **Azure AI Foundry** for LLM inference
            - **Azure AI Search** for vector search
            - **LangChain** for RAG orchestration
            
            Ask questions about your enterprise documents
            and get accurate answers with source citations.
            """)
        
        return top_k, min_score, show_sources, show_metadata


def display_chat_message(role: str, content: str, sources: str = None):
    """Display a chat message."""
    if role == "user":
        st.markdown(
            f'<div class="chat-message user-message"><strong>You:</strong><br/>{content}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="chat-message assistant-message"><strong>Assistant:</strong><br/>{content}</div>',
            unsafe_allow_html=True
        )
        
        if sources:
            with st.expander("📄 View Sources"):
                st.markdown(f'<div class="source-box">{sources}</div>', unsafe_allow_html=True)


def display_chat_history():
    """Display chat history."""
    if st.session_state.chat_history:
        st.subheader("💬 Conversation History")
        
        for message in st.session_state.chat_history:
            display_chat_message(
                role=message["role"],
                content=message["content"],
                sources=message.get("sources")
            )


def main():
    """Main application logic."""
    initialize_session_state()
    
    # Display header
    display_header()
    
    # Initialize RAG chain
    if not initialize_rag_chain():
        st.stop()
    
    # Display sidebar
    top_k, min_score, show_sources, show_metadata = display_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("💡 Ask a Question")
        
        # Sample questions
        with st.expander("📝 Try these sample questions"):
            st.markdown("""
            - What is the company vacation policy?
            - How do I submit an expense report?
            - What are the requirements for remote work?
            - What is the process for requesting time off?
            - What are the company's core values?
            """)
    
    # Query input
    query = st.text_area(
        "Enter your question:",
        placeholder="Ask anything about the enterprise documents...",
        height=100,
        key="query_input"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
    
    with col_btn1:
        submit_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    with col_btn2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    
    if clear_button:
        st.session_state.query_input = ""
        st.rerun()
    
    # Process query
    if submit_button and query:
        with st.spinner("Searching documents and generating answer..."):
            try:
                # Update RAG chain settings
                st.session_state.rag_chain.top_k = top_k
                st.session_state.rag_chain.min_relevance_score = min_score
                
                # Query
                response = st.session_state.rag_chain.query(
                    question=query,
                    return_sources=show_sources
                )
                
                # Update session state
                st.session_state.query_count += 1
                st.session_state.total_tokens += response.get("tokens_used", 0)
                
                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": query
                })
                
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sources": response.get("sources", "")
                })
                
                # Display response
                st.markdown("---")
                st.subheader("✅ Answer")
                st.markdown(response["answer"])
                
                # Display sources
                if show_sources and response.get("sources"):
                    st.markdown("---")
                    st.subheader("📚 Sources")
                    st.markdown(f'<div class="source-box">{response["sources"]}</div>', unsafe_allow_html=True)
                
                # Display metadata
                if show_metadata:
                    st.markdown("---")
                    st.subheader("📊 Query Metadata")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Documents Retrieved", response.get("num_sources", 0))
                    
                    with col2:
                        st.metric("Retrieval Time", f"{response.get('retrieval_time', 0):.2f}s")
                    
                    with col3:
                        st.metric("Generation Time", f"{response.get('generation_time', 0):.2f}s")
                    
                    with col4:
                        st.metric("Tokens Used", response.get("tokens_used", 0))
                    
                    # Relevance scores
                    if response.get("relevance_scores"):
                        st.subheader("Relevance Scores")
                        scores = response["relevance_scores"]
                        st.bar_chart({"Score": scores})
                
                logger.info(f"Query processed successfully: {query[:50]}...")
            
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.error(f"Query processing error: {e}", exc_info=True)
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("---")
        display_chat_history()


if __name__ == "__main__":
    main()
