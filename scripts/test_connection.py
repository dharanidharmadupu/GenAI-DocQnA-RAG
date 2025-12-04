"""Test Azure connectivity and configuration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import get_config
from src.generation.llm_client import AzureLLMClient
from src.ingestion.embedder import Embedder
from src.retrieval.search_client import SearchIndexManager
from src.utils.logger import setup_logger, get_logger

setup_logger(log_level="INFO")
logger = get_logger(__name__)


def test_configuration():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    
    try:
        config = get_config()
        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  AI Foundry Endpoint: {config.ai_foundry.endpoint}")
        logger.info(f"  Search Endpoint: {config.search.endpoint}")
        logger.info(f"  Index Name: {config.search.index_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


def test_llm_connection():
    """Test LLM connection."""
    logger.info("\nTesting LLM connection...")
    
    try:
        client = AzureLLMClient()
        
        # Test simple generation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!' in one word."}
        ]
        
        response = client.generate(messages, max_tokens=10)
        logger.info(f"✓ LLM connection successful")
        logger.info(f"  Response: {response}")
        return True
    except Exception as e:
        logger.error(f"✗ LLM connection test failed: {e}")
        return False


def test_embedding_generation():
    """Test embedding generation."""
    logger.info("\nTesting embedding generation...")
    
    try:
        embedder = Embedder()
        
        # Test embedding
        text = "This is a test document."
        embedding = embedder.embed_text(text)
        
        logger.info(f"✓ Embedding generation successful")
        logger.info(f"  Embedding dimension: {len(embedding)}")
        logger.info(f"  First 5 values: {embedding[:5]}")
        return True
    except Exception as e:
        logger.error(f"✗ Embedding test failed: {e}")
        return False


def test_search_service():
    """Test Azure AI Search service."""
    logger.info("\nTesting Azure AI Search service...")
    
    try:
        manager = SearchIndexManager()
        config = get_config()
        
        index_name = config.search.index_name
        exists = manager.index_exists(index_name)
        
        logger.info(f"✓ Search service connection successful")
        logger.info(f"  Index '{index_name}' exists: {exists}")
        
        if not exists:
            logger.warning("  ⚠ Index does not exist. Run 'python scripts/setup_search_index.py' to create it.")
        
        return True
    except Exception as e:
        logger.error(f"✗ Search service test failed: {e}")
        return False


def main():
    """Run all connection tests."""
    logger.info("="*80)
    logger.info("Azure Connectivity Test")
    logger.info("="*80)
    
    results = {
        "Configuration": test_configuration(),
        "LLM Connection": test_llm_connection(),
        "Embedding Generation": test_embedding_generation(),
        "Search Service": test_search_service()
    }
    
    logger.info("\n" + "="*80)
    logger.info("Test Summary")
    logger.info("="*80)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = "green" if result else "red"
        logger.info(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ All tests passed! System is ready to use.")
        sys.exit(0)
    else:
        logger.error("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
