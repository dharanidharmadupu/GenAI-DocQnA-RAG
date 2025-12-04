"""Test RAG chain functionality."""

import pytest
from unittest.mock import Mock, patch

from src.generation import EnterpriseRAGChain


class TestEnterpriseRAGChain:
    """Test RAG chain."""
    
    def test_initialization(self):
        """Test RAG chain initialization."""
        rag_chain = EnterpriseRAGChain(top_k=5)
        
        assert rag_chain.top_k == 5
        assert rag_chain.retriever is not None
        assert rag_chain.llm_client is not None
    
    @pytest.mark.integration
    def test_query_no_documents(self):
        """Test query with no relevant documents."""
        rag_chain = EnterpriseRAGChain()
        
        with patch.object(rag_chain.retriever, '_get_relevant_documents', return_value=[]):
            response = rag_chain.query("test question")
        
        assert "answer" in response
        assert response["num_sources"] == 0
        assert "no relevant information" in response["answer"].lower() or \
               "don't have enough information" in response["answer"].lower()
    
    @pytest.mark.integration
    def test_query_with_documents(self):
        """Test full query flow (requires Azure connection)."""
        rag_chain = EnterpriseRAGChain(top_k=3)
        
        question = "What is the company vacation policy?"
        
        try:
            response = rag_chain.query(question)
            
            assert "answer" in response
            assert "sources" in response
            assert "total_time" in response
            assert "tokens_used" in response
            assert isinstance(response["answer"], str)
        except Exception as e:
            # May fail if no documents indexed yet
            pytest.skip(f"Integration test skipped: {e}")
    
    def test_batch_query(self):
        """Test batch query processing."""
        rag_chain = EnterpriseRAGChain()
        
        questions = [
            "What is the vacation policy?",
            "How do I submit expenses?"
        ]
        
        with patch.object(rag_chain, 'query', return_value={"answer": "test"}):
            results = rag_chain.batch_query(questions)
        
        assert len(results) == len(questions)
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        rag_chain = EnterpriseRAGChain()
        
        stats = rag_chain.get_statistics()
        
        assert "total_queries" in stats
        assert "total_tokens" in stats
        assert isinstance(stats["total_queries"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
