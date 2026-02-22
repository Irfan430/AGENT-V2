"""
Enhanced LLM Client with support for multiple LLM APIs.
Supports DeepSeek, OpenAI, Gemini, and other OpenAI-compatible APIs.
"""

import os
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
import logging
from abc import ABC, abstractmethod

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

class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def chat_completion_async(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """Asynchronous chat completion request."""
        pass
    
    @abstractmethod
    async def stream_chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion response token by token."""
        pass
    
    @abstractmethod
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """Synchronous chat completion request."""
        pass

class DeepSeekClient(BaseLLMClient):
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
        self.provider = "deepseek"
        
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
        """Synchronous chat completion request."""
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
        """Asynchronous chat completion request."""
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
        """Stream chat completion response token by token."""
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

class OpenAIClient(BaseLLMClient):
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: Model name to use (default: gpt-4-turbo)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        self.provider = "openai"
        
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        logger.info(f"OpenAI client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """Synchronous chat completion request."""
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
        """Asynchronous chat completion request."""
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
        """Stream chat completion response token by token."""
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

class GeminiClient(BaseLLMClient):
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash"):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If not provided, reads from GEMINI_API_KEY env var.
            model: Model name to use (default: gemini-2.0-flash)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.provider = "gemini"
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"Gemini client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """Synchronous chat completion request."""
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
        """Asynchronous chat completion request."""
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
        """Stream chat completion response token by token."""
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

class CustomOpenAICompatibleClient(BaseLLMClient):
    """Client for any OpenAI-compatible API."""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        """
        Initialize a custom OpenAI-compatible client.
        
        Args:
            api_key: API key for the service
            base_url: Base URL for the API
            model: Model name to use
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.provider = "custom"
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(f"Custom OpenAI-compatible client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
        """Synchronous chat completion request."""
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
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
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
        """Asynchronous chat completion request."""
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
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
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
        """Stream chat completion response token by token."""
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

# Global client instance
_client: Optional[BaseLLMClient] = None

def get_llm_client() -> BaseLLMClient:
    """Get or create the global LLM client."""
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client

def initialize_llm_client(
    provider: str = "deepseek",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> BaseLLMClient:
    """
    Initialize the global LLM client with custom settings.
    
    Args:
        provider: LLM provider ('deepseek', 'openai', 'gemini', or 'custom')
        api_key: API key for the provider
        model: Model name to use
        base_url: Base URL (required for 'custom' provider)
    
    Returns:
        Initialized LLM client
    """
    global _client
    
    provider = provider.lower()
    
    if provider == "deepseek":
        model = model or "deepseek-chat"
        _client = DeepSeekClient(api_key=api_key, model=model)
    elif provider == "openai":
        model = model or "gpt-4-turbo"
        _client = OpenAIClient(api_key=api_key, model=model)
    elif provider == "gemini":
        model = model or "gemini-2.0-flash"
        _client = GeminiClient(api_key=api_key, model=model)
    elif provider == "custom":
        if not base_url:
            raise ValueError("base_url is required for custom provider")
        if not api_key:
            raise ValueError("api_key is required for custom provider")
        if not model:
            raise ValueError("model is required for custom provider")
        _client = CustomOpenAICompatibleClient(api_key=api_key, base_url=base_url, model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: deepseek, openai, gemini, custom")
    
    logger.info(f"LLM client initialized with provider: {provider}, model: {_client.model}")
    return _client

def list_supported_providers() -> List[str]:
    """Get list of supported LLM providers."""
    return ["deepseek", "openai", "gemini", "custom"]
