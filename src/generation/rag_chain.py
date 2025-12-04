"""RAG chain implementation for enterprise Q&A."""

import time
from typing import Dict, List, Optional, Any

from langchain.schema import Document

from ..retrieval.retriever import EnterpriseRetriever
from .llm_client import AzureLLMClient
from .prompts import (
    get_rag_prompt_template,
    get_no_context_prompt,
    format_context,
    format_sources
)
from ..utils.logger import get_logger
from ..utils.metrics import QueryMetrics, get_metrics_collector

logger = get_logger(__name__)


class EnterpriseRAGChain:
    """RAG chain for enterprise document Q&A."""
    
    def __init__(
        self,
        index_name: Optional[str] = None,
        top_k: int = 5,
        min_relevance_score: float = 0.0
    ):
        """
        Initialize RAG chain.
        
        Args:
            index_name: Name of search index (optional)
            top_k: Number of documents to retrieve
            min_relevance_score: Minimum relevance score threshold
        """
        self.retriever = EnterpriseRetriever(
            index_name=index_name,
            top_k=top_k
        )
        self.llm_client = AzureLLMClient()
        self.prompt_template = get_rag_prompt_template()
        
        self.top_k = top_k
        self.min_relevance_score = min_relevance_score
        
        self.logger = logger
        self.metrics_collector = get_metrics_collector()
    
    def query(
        self,
        question: str,
        top_k: Optional[int] = None,
        return_sources: bool = True,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Query the RAG system.
        
        Args:
            question: User question
            top_k: Number of documents to retrieve (optional)
            return_sources: Whether to return source documents
            chat_history: Previous conversation history (optional)
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        self.logger.info(f"Processing query: {question[:100]}...")
        
        start_time = time.time()
        metrics = QueryMetrics(query=question)
        
        try:
            # Step 1: Retrieve relevant documents
            retrieval_start = time.time()
            
            if top_k:
                self.retriever.top_k = top_k
            
            documents = self.retriever._get_relevant_documents(question)
            
            metrics.retrieval_time = time.time() - retrieval_start
            metrics.num_results = len(documents)
            
            # Check if we have relevant documents
            if not documents:
                self.logger.warning("No relevant documents found")
                response = get_no_context_prompt()
                
                metrics.total_time = time.time() - start_time
                self.metrics_collector.record_query(metrics)
                
                return {
                    "answer": response,
                    "sources": [],
                    "num_sources": 0,
                    "relevance_scores": [],
                    "retrieval_time": metrics.retrieval_time,
                    "generation_time": 0.0,
                    "total_time": metrics.total_time,
                    "tokens_used": 0
                }
            
            # Filter by relevance score if threshold is set
            if self.min_relevance_score > 0:
                documents = [
                    doc for doc in documents
                    if doc.metadata.get("score", 0) >= self.min_relevance_score
                ]
            
            if not documents:
                self.logger.warning("No documents meet minimum relevance threshold")
                response = get_no_context_prompt()
                
                metrics.total_time = time.time() - start_time
                self.metrics_collector.record_query(metrics)
                
                return {
                    "answer": response,
                    "sources": [],
                    "num_sources": 0,
                    "relevance_scores": [],
                    "retrieval_time": metrics.retrieval_time,
                    "generation_time": 0.0,
                    "total_time": metrics.total_time,
                    "tokens_used": 0
                }
            
            # Step 2: Format context
            context_docs = [
                {
                    "content": doc.page_content,
                    "source_file": doc.metadata.get("source_file", "Unknown"),
                    "page_number": doc.metadata.get("page_number", "N/A"),
                    "score": doc.metadata.get("score", 0.0)
                }
                for doc in documents
            ]
            
            context = format_context(context_docs)
            
            # Step 3: Generate answer
            generation_start = time.time()
            
            # Prepare messages
            messages = self.prompt_template.format_messages(
                context=context,
                question=question
            )
            
            # Convert to format expected by OpenAI
            messages_dict = [
                {"role": msg.type if msg.type != "human" else "user", "content": msg.content}
                for msg in messages
            ]
            
            # Generate response with metadata
            response_data = self.llm_client.generate_with_metadata(messages_dict)
            
            metrics.generation_time = time.time() - generation_start
            metrics.tokens_used = response_data["total_tokens"]
            
            # Step 4: Prepare response
            answer = response_data["content"]
            sources = format_sources(context_docs) if return_sources else ""
            
            metrics.total_time = time.time() - start_time
            
            # Calculate average relevance score
            relevance_scores = [doc["score"] for doc in context_docs]
            metrics.relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            # Record metrics
            self.metrics_collector.record_query(metrics)
            
            self.logger.info(
                f"Query completed in {metrics.total_time:.2f}s "
                f"({metrics.retrieval_time:.2f}s retrieval, {metrics.generation_time:.2f}s generation)"
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "source_documents": context_docs if return_sources else [],
                "num_sources": len(documents),
                "relevance_scores": relevance_scores,
                "retrieval_time": metrics.retrieval_time,
                "generation_time": metrics.generation_time,
                "total_time": metrics.total_time,
                "tokens_used": metrics.tokens_used,
                "prompt_tokens": response_data["prompt_tokens"],
                "completion_tokens": response_data["completion_tokens"]
            }
        
        except Exception as e:
            self.logger.error(f"Error processing query: {e}", exc_info=True)
            
            metrics.error = str(e)
            metrics.total_time = time.time() - start_time
            self.metrics_collector.record_query(metrics)
            
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": "",
                "source_documents": [],
                "num_sources": 0,
                "relevance_scores": [],
                "retrieval_time": 0.0,
                "generation_time": 0.0,
                "total_time": metrics.total_time,
                "tokens_used": 0,
                "error": str(e)
            }
    
    def batch_query(
        self,
        questions: List[str],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple queries in batch.
        
        Args:
            questions: List of questions
            top_k: Number of documents to retrieve per question
        
        Returns:
            List of response dictionaries
        """
        self.logger.info(f"Processing batch of {len(questions)} questions")
        
        results = []
        for i, question in enumerate(questions, 1):
            self.logger.info(f"Processing question {i}/{len(questions)}")
            result = self.query(question, top_k=top_k)
            results.append(result)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.metrics_collector.get_summary()


if __name__ == "__main__":
    # Test RAG chain
    from dotenv import load_dotenv
    load_dotenv()
    
    rag_chain = EnterpriseRAGChain(top_k=3)
    
    # Test query
    question = "What is the company vacation policy?"
    
    print(f"Question: {question}\n")
    
    response = rag_chain.query(question)
    
    print(f"Answer:\n{response['answer']}\n")
    print(f"\nSources:\n{response['sources']}\n")
    print(f"Time: {response['total_time']:.2f}s (retrieval: {response['retrieval_time']:.2f}s, generation: {response['generation_time']:.2f}s)")
    print(f"Tokens used: {response['tokens_used']}")
