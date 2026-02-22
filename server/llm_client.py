"""
DeepSeek API client for language model interactions.
Handles API calls, streaming, and error handling.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class Message(BaseModel):
    """Message model for API interactions."""
    role: str  # "system", "user", "assistant"
    content: str

class LLMResponse(BaseModel):
    """Response model from LLM."""
    content: str
    finish_reason: str
    usage: Optional[Dict[str, int]] = None

class DeepSeekClient:
    """
    Client for interacting with DeepSeek API.
    Provides both sync and async methods for LLM calls.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        """
        Initialize the DeepSeek client.
        
        Args:
            api_key: DeepSeek API key. If not provided, reads from LLM_API_KEY env var.
            model: Model name to use (default: deepseek-chat)
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key not found. Set LLM_API_KEY environment variable.")
        
        self.model = model
        self.base_url = "https://api.deepseek.com"
        
        # Initialize both sync and async clients
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"DeepSeek client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """
        Synchronous chat completion request.
        
        Args:
            messages: List of messages in conversation
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            
        Returns:
            LLMResponse with the model's response
        """
        try:
            message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream
            )
            
            if stream:
                # For streaming, we need to collect the response
                content = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                
                return LLMResponse(
                    content=content,
                    finish_reason="stop",
                    usage=None
                )
            else:
                return LLMResponse(
                    content=response.choices[0].message.content,
                    finish_reason=response.choices[0].finish_reason,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                )
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise
    
    async def chat_completion_async(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """
        Asynchronous chat completion request.
        
        Args:
            messages: List of messages in conversation
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            stream: Whether to stream the response
            
        Returns:
            LLMResponse with the model's response
        """
        try:
            message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream
            )
            
            if stream:
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                
                return LLMResponse(
                    content=content,
                    finish_reason="stop",
                    usage=None
                )
            else:
                return LLMResponse(
                    content=response.choices[0].message.content,
                    finish_reason=response.choices[0].finish_reason,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                )
        except Exception as e:
            logger.error(f"Error in async chat completion: {str(e)}")
            raise
    
    async def stream_chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response token by token.
        
        Args:
            messages: List of messages in conversation
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            
        Yields:
            Response tokens as they arrive
        """
        try:
            message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=message_dicts,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error in stream chat completion: {str(e)}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Uses simple approximation: ~4 characters per token.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "api_key_set": bool(self.api_key)
        }

# Global client instance
_client: Optional[DeepSeekClient] = None

def get_llm_client() -> DeepSeekClient:
    """Get or create the global LLM client."""
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client

def initialize_llm_client(api_key: Optional[str] = None, model: str = "deepseek-chat") -> DeepSeekClient:
    """Initialize the global LLM client with custom settings."""
    global _client
    _client = DeepSeekClient(api_key=api_key, model=model)
    return _client
