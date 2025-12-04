"""Prompt templates for RAG system."""

from typing import List, Dict
from langchain.prompts import ChatPromptTemplate, PromptTemplate

from ..config import get_config


def get_system_prompt() -> str:
    """
    Get system prompt from config or use default.
    
    Returns:
        System prompt text
    """
    config = get_config()
    
    default_prompt = """You are an intelligent assistant helping users find information from enterprise documents.

Your role is to:
1. Provide accurate, concise answers based ONLY on the provided context
2. Cite sources by mentioning the document name and page number
3. If the answer is not in the context, clearly state "I don't have enough information to answer that question"
4. Be professional and helpful
5. Format answers clearly with proper structure

Remember: Only use information from the provided context. Do not make up information."""
    
    return config.get_prompt("system_prompt") or default_prompt


def get_rag_prompt_template() -> ChatPromptTemplate:
    """
    Get RAG prompt template for question answering.
    
    Returns:
        ChatPromptTemplate for RAG
    """
    config = get_config()
    
    # Get template from config or use default
    default_template = """Context from enterprise documents:
{context}

Question: {question}

Instructions:
- Answer the question using ONLY the information from the context above
- Include citations (document name and page number) for each piece of information
- If the context doesn't contain the answer, say so clearly
- Be concise but comprehensive
- Format your answer in a clear, structured way

Answer:"""
    
    template = config.get_prompt("rag_prompt") or default_template
    
    return ChatPromptTemplate.from_messages([
        ("system", get_system_prompt()),
        ("human", template)
    ])


def get_no_context_prompt() -> str:
    """
    Get prompt for when no relevant context is found.
    
    Returns:
        No context prompt text
    """
    config = get_config()
    
    default_prompt = """I apologize, but I couldn't find relevant information in the available documents to answer your question.

You might want to:
- Rephrase your question to be more specific
- Check if the relevant documents have been uploaded to the system
- Contact the document administrator for additional resources

Please try asking your question in a different way, or let me know if you'd like help with something else."""
    
    return config.get_prompt("no_context_prompt") or default_prompt


def format_context(documents: List[Dict]) -> str:
    """
    Format retrieved documents into context string.
    
    Args:
        documents: List of retrieved document dictionaries
    
    Returns:
        Formatted context string
    """
    if not documents:
        return "No relevant documents found."
    
    context_parts = []
    
    for i, doc in enumerate(documents, 1):
        source = doc.get("source_file", "Unknown")
        page = doc.get("page_number", "N/A")
        content = doc.get("content", "")
        
        context_parts.append(
            f"[Document {i}]\n"
            f"Source: {source} (Page {page})\n"
            f"Content: {content}\n"
        )
    
    return "\n---\n".join(context_parts)


def format_sources(documents: List[Dict]) -> str:
    """
    Format source citations for display.
    
    Args:
        documents: List of retrieved document dictionaries
    
    Returns:
        Formatted sources string
    """
    if not documents:
        return "No sources available."
    
    sources = []
    seen = set()
    
    for doc in documents:
        source = doc.get("source_file", "Unknown")
        page = doc.get("page_number", "N/A")
        key = f"{source}:{page}"
        
        if key not in seen:
            sources.append(f"- {source} (Page {page})")
            seen.add(key)
    
    return "\n".join(sources)


def create_chat_history_prompt(
    chat_history: List[Dict[str, str]],
    max_history: int = 5
) -> List[Dict[str, str]]:
    """
    Create chat history for context-aware conversations.
    
    Args:
        chat_history: List of previous messages
        max_history: Maximum number of history messages to include
    
    Returns:
        Formatted chat history
    """
    # Keep only recent history
    recent_history = chat_history[-max_history:] if len(chat_history) > max_history else chat_history
    
    return recent_history


def get_evaluation_prompt() -> str:
    """
    Get prompt for evaluating answer quality.
    
    Returns:
        Evaluation prompt
    """
    return """Evaluate the following answer based on these criteria:

1. Accuracy: Does the answer correctly use information from the context?
2. Completeness: Does it fully address the question?
3. Citation: Are sources properly cited?
4. Clarity: Is the answer well-structured and easy to understand?

Question: {question}
Context: {context}
Answer: {answer}

Provide a score from 1-10 and brief explanation for each criterion."""


# Pre-defined prompt templates
CONDENSE_QUESTION_PROMPT = PromptTemplate(
    input_variables=["chat_history", "question"],
    template="""Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History:
{chat_history}

Follow Up Question: {question}

Standalone Question:"""
)


MULTI_QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an AI assistant. Generate 3 different versions of the given question to retrieve relevant documents from a vector database.
Provide these alternative questions separated by newlines.

Original question: {question}

Alternative questions:"""
)


if __name__ == "__main__":
    # Test prompt templates
    template = get_rag_prompt_template()
    print("RAG Prompt Template:")
    print(template.format_messages(
        context="Sample context",
        question="Sample question"
    ))
    
    print("\n" + "="*80 + "\n")
    
    print("No Context Prompt:")
    print(get_no_context_prompt())
