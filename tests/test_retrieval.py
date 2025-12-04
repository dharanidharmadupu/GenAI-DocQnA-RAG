"""Test retrieval functionality."""

import pytest
from unittest.mock import Mock, patch

from src.retrieval import AzureSearchRetriever, EnterpriseRetriever


class TestAzureSearchRetriever:
    """Test Azure Search retriever."""
    
    def test_initialization(self):
        """Test retriever initialization."""
        retriever = AzureSearchRetriever()
        
        assert retriever.index_name is not None
        assert retriever.endpoint is not None
    
    @pytest.mark.integration
    def test_vector_search(self):
        """Test vector search (requires Azure connection)."""
        retriever = AzureSearchRetriever()
        
        # Mock query vector (1536 dimensions)
        query_vector = [0.1] * 1536
        
        results = retriever.vector_search(query_vector, top_k=3)
        
        assert isinstance(results, list)
        # Results may be empty if index is empty, that's ok for test
    
    @pytest.mark.integration
    def test_hybrid_search(self):
        """Test hybrid search (requires Azure connection)."""
        retriever = AzureSearchRetriever()
        
        query_text = "test query"
        query_vector = [0.1] * 1536
        
        results = retriever.hybrid_search(query_text, query_vector, top_k=3)
        
        assert isinstance(results, list)


class TestEnterpriseRetriever:
    """Test enterprise retriever."""
    
    def test_initialization(self):
        """Test retriever initialization."""
        retriever = EnterpriseRetriever(top_k=5)
        
        assert retriever.top_k == 5
        assert retriever.embedder is not None
        assert retriever.search_retriever is not None
    
    @pytest.mark.integration
    def test_get_relevant_documents(self):
        """Test document retrieval (requires Azure connection)."""
        retriever = EnterpriseRetriever(top_k=3)
        
        query = "What is the vacation policy?"
        documents = retriever._get_relevant_documents(query)
        
        assert isinstance(documents, list)
        # Documents may be empty if index is empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
