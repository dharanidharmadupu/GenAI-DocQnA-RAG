"""Azure AI Foundry LLM client."""

from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AzureLLMClient:
    """Client for Azure AI Foundry LLM."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        config = get_config()
        
        self.client = AzureOpenAI(
            api_key=config.ai_foundry.key,
            api_version=config.ai_foundry.api_version,
            azure_endpoint=config.ai_foundry.endpoint
        )
        
        self.deployment_name = config.ai_foundry.gpt_deployment_name
        self.temperature = config.rag.temperature
        self.max_tokens = config.rag.max_tokens
        
        self.logger = logger
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
            stream: Whether to stream the response
        
        Returns:
            Generated text
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response  # Return generator for streaming
            else:
                return response.choices[0].message.content
        
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            raise
    
    def generate_with_metadata(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate response with metadata (tokens, finish reason, etc.).
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature (optional)
            max_tokens: Maximum tokens to generate (optional)
        
        Returns:
            Dictionary with response and metadata
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "model": response.model
            }
        
        except Exception as e:
            self.logger.error(f"Error generating response with metadata: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    def validate_deployment(self) -> bool:
        """
        Validate that the deployment is accessible.
        
        Returns:
            True if deployment is accessible, False otherwise
        """
        try:
            messages = [{"role": "user", "content": "Hello"}]
            response = self.generate(messages, max_tokens=10)
            self.logger.info("LLM deployment validated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Deployment validation failed: {e}")
            return False


if __name__ == "__main__":
    # Test LLM client
    from dotenv import load_dotenv
    load_dotenv()
    
    client = AzureLLMClient()
    
    # Test simple generation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Azure AI?"}
    ]
    
    response = client.generate_with_metadata(messages)
    print(f"Response: {response['content']}")
    print(f"Tokens used: {response['total_tokens']}")
