"""LangChain retriever wrapper for Azure AI Search."""

from typing import List, Optional
from langchain.schema import Document
from langchain.schema.retriever import BaseRetriever

from ..ingestion.embedder import Embedder
from .search_client import AzureSearchRetriever
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EnterpriseRetriever(BaseRetriever):
    """
    LangChain-compatible retriever for enterprise documents.
    Combines Azure AI Search with embedding generation.
    """
    
    embedder: Embedder
    search_retriever: AzureSearchRetriever
    top_k: int = 5
    
    def __init__(
        self,
        index_name: Optional[str] = None,
        top_k: int = 5
    ):
        """
        Initialize enterprise retriever.
        
        Args:
            index_name: Name of the search index
            top_k: Number of documents to retrieve
        """
        super().__init__(
            embedder=Embedder(),
            search_retriever=AzureSearchRetriever(index_name=index_name),
            top_k=top_k
        )
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: Query string
        
        Returns:
            List of relevant documents
        """
        logger.info(f"Retrieving documents for query: {query[:100]}...")
        
        try:
            # Generate query embedding
            query_vector = self.embedder.embed_query(query)
            
            # Search
            results = self.search_retriever.search(
                query_text=query,
                query_vector=query_vector,
                top_k=self.top_k
            )
            
            # Convert to LangChain documents
            documents = []
            for result in results:
                doc = Document(
                    page_content=result["content"],
                    metadata={
                        "id": result["id"],
                        "title": result["title"],
                        "source_file": result["source_file"],
                        "page_number": result["page_number"],
                        "chunk_id": result["chunk_id"],
                        "score": result["score"],
                        "reranker_score": result.get("reranker_score")
                    }
                )
                documents.append(doc)
            
            logger.info(f"Retrieved {len(documents)} documents")
            return documents
        
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """
        Async version of document retrieval.
        
        Args:
            query: Query string
        
        Returns:
            List of relevant documents
        """
        # For now, just call sync version
        return self._get_relevant_documents(query)


if __name__ == "__main__":
    # Test retriever
    from dotenv import load_dotenv
    load_dotenv()
    
    retriever = EnterpriseRetriever(top_k=3)
    
    query = "What is the company vacation policy?"
    documents = retriever._get_relevant_documents(query)
    
    print(f"\nFound {len(documents)} documents:")
    for i, doc in enumerate(documents, 1):
        print(f"\n{i}. {doc.metadata['source_file']} (page {doc.metadata['page_number']})")
        print(f"   Score: {doc.metadata['score']:.4f}")
        print(f"   Content: {doc.page_content[:200]}...")
