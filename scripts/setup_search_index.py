"""Setup Azure AI Search index."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import get_config
from src.retrieval.search_client import SearchIndexManager
from src.utils.logger import setup_logger, get_logger

setup_logger(log_level="INFO")
logger = get_logger(__name__)


def main():
    """Setup search index."""
    logger.info("Setting up Azure AI Search index...")
    
    try:
        config = get_config()
        manager = SearchIndexManager()
        
        index_name = config.search.index_name
        
        if manager.index_exists(index_name):
            logger.info(f"Index '{index_name}' already exists")
            
            response = input(f"Do you want to delete and recreate the index? (y/N): ")
            if response.lower() == 'y':
                logger.info(f"Deleting existing index...")
                manager.delete_index(index_name)
                logger.info(f"Creating new index...")
                manager.create_index(index_name)
                logger.info(f"✓ Index recreated successfully")
            else:
                logger.info("Keeping existing index")
        else:
            logger.info(f"Creating index: {index_name}")
            manager.create_index(index_name)
            logger.info(f"✓ Index created successfully")
        
        logger.info(f"Index endpoint: {config.search.endpoint}")
        logger.info(f"Index name: {index_name}")
    
    except Exception as e:
        logger.error(f"Failed to setup index: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
