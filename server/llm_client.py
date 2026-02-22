"""
Multi-LLM API client for language model interactions.
Supports DeepSeek, OpenAI, Gemini, and custom OpenAI-compatible APIs.
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel

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
    provider: str

class BaseLLMClient:
    """Base class for LLM clients."""
    async def chat_completion_async(self, messages: List[Message], **kwargs) -> LLMResponse:
        raise NotImplementedError
    
    async def stream_chat_completion(self, messages: List[Message], **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError

class OpenAICompatibleClient(BaseLLMClient):
    """Client for OpenAI-compatible APIs (DeepSeek, OpenAI, etc.)"""
    
    def __init__(self, api_key: str, base_url: str, model: str, provider: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.provider = provider
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        logger.info(f"{provider} client initialized with model: {self.model}")

    async def chat_completion_async(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95,
        stream: bool = False
    ) -> LLMResponse:
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
                    usage=None,
                    provider=self.provider
                )
            else:
                return LLMResponse(
                    content=response.choices[0].message.content,
                    finish_reason=response.choices[0].finish_reason,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    } if response.usage else None,
                    provider=self.provider
                )
        except Exception as e:
            logger.error(f"Error in {self.provider} async chat completion: {str(e)}")
            raise

    async def stream_chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        top_p: float = 0.95
    ) -> AsyncGenerator[str, None]:
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
            logger.error(f"Error in {self.provider} stream chat completion: {str(e)}")
            raise

class LLMClientManager:
    """Manages multiple LLM providers and provides a unified interface."""
    
    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        self._initialize_from_env()

    def _initialize_from_env(self):
        """Initialize clients based on environment variables."""
        # DeepSeek
        ds_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
        if ds_key:
            self.clients["deepseek"] = OpenAICompatibleClient(
                api_key=ds_key,
                base_url="https://api.deepseek.com",
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                provider="deepseek"
            )
        
        # OpenAI
        oa_key = os.getenv("OPENAI_API_KEY")
        if oa_key:
            self.clients["openai"] = OpenAICompatibleClient(
                api_key=oa_key,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                provider="openai"
            )
            
        # Custom
        custom_key = os.getenv("CUSTOM_LLM_API_KEY")
        if custom_key:
            self.clients["custom"] = OpenAICompatibleClient(
                api_key=custom_key,
                base_url=os.getenv("CUSTOM_LLM_BASE_URL", ""),
                model=os.getenv("CUSTOM_LLM_MODEL", ""),
                provider="custom"
            )

    def get_client(self, provider: Optional[str] = None) -> BaseLLMClient:
        provider = provider or self.default_provider
        if provider not in self.clients:
            if not self.clients:
                raise ValueError("No LLM clients initialized. Set API keys in environment.")
            # Fallback to first available client
            return list(self.clients.values())[0]
        return self.clients[provider]

    async def chat_completion_async(self, messages: List[Message], provider: Optional[str] = None, **kwargs) -> LLMResponse:
        client = self.get_client(provider)
        return await client.chat_completion_async(messages, **kwargs)

    async def stream_chat_completion(self, messages: List[Message], provider: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        client = self.get_client(provider)
        async for chunk in client.stream_chat_completion(messages, **kwargs):
            yield chunk

# Global manager instance
_manager: Optional[LLMClientManager] = None

def get_llm_client() -> LLMClientManager:
    """Get or create the global LLM client manager."""
    global _manager
    if _manager is None:
        _manager = LLMClientManager()
    return _manager

def initialize_llm_client(api_key: Optional[str] = None, provider: str = "deepseek", **kwargs) -> LLMClientManager:
    """Initialize the global LLM client manager."""
    global _manager
    if _manager is None:
        _manager = LLMClientManager()
    
    # If explicit API key provided, override or add client
    if api_key:
        if provider == "deepseek":
            _manager.clients["deepseek"] = OpenAICompatibleClient(
                api_key=api_key,
                base_url="https://api.deepseek.com",
                model=kwargs.get("model", "deepseek-chat"),
                provider="deepseek"
            )
        elif provider == "openai":
            _manager.clients["openai"] = OpenAICompatibleClient(
                api_key=api_key,
                base_url="https://api.openai.com/v1",
                model=kwargs.get("model", "gpt-4-turbo"),
                provider="openai"
            )
    
    _manager.default_provider = provider
    return _manager
