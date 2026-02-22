import asyncio
import logging
import json
import uuid
import os
from typing import Dict, Any, Optional, List, Set
from fastapi import FastAPI, Request, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from contextlib import asynccontextmanager
import uvicorn

from server.agent_orchestrator import get_orchestrator
from server.agent_state import AgentState
from server.llm_client import get_llm_client, initialize_llm_client
from server.monitoring import get_monitor
from server.security import RateLimiter, InputValidator, get_rate_limiter, get_security_auditor
from server.agent_config import AGENT_NAME, AGENT_VERSION, AGENT_DESCRIPTION
from server.tool_manager import get_tool_manager
from server.task_scheduler import initialize_task_scheduler, shutdown_task_scheduler
from server.memory_manager import get_memory_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize security components
rate_limiter = get_rate_limiter()
input_validator = InputValidator()
security_auditor = get_security_auditor()
monitor = get_monitor()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"WebSocket connected: {conversation_id}")
    
    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"WebSocket disconnected: {conversation_id}")
    
    async def send_json(self, conversation_id: str, data: dict):
        if conversation_id in self.active_connections:
            try:
                await self.active_connections[conversation_id].send_json(data)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.disconnect(conversation_id)

ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info(f"Starting {AGENT_NAME} v{AGENT_VERSION}")
    
    # Initialize LLM client with the provided API key
    openai_key = os.getenv("OPENAI_API_KEY")
    llm_key = os.getenv("LLM_API_KEY")
    api_key = openai_key or llm_key
    
    if not api_key:
        logger.error("No API key found (OPENAI_API_KEY or LLM_API_KEY). Agent will not function correctly.")
    else:
        from server.llm_client import OpenAICompatibleClient, get_llm_client
        
        provider = os.getenv("DEFAULT_LLM_PROVIDER", "deepseek")
        mgr = get_llm_client()
        
        # Initialize DeepSeek if key available
        deepseek_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
        if deepseek_key:
            deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            mgr.clients["deepseek"] = OpenAICompatibleClient(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                model=deepseek_model,
                provider="deepseek"
            )
            if provider == "deepseek":
                mgr.default_provider = "deepseek"
        
        # Initialize OpenAI if key available
        if openai_key:
            openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
            mgr.clients["openai"] = OpenAICompatibleClient(
                api_key=openai_key,
                base_url=openai_base,
                model=openai_model,
                provider="openai"
            )
            if provider == "openai":
                mgr.default_provider = "openai"
        
        # Set default provider
        if provider in mgr.clients:
            mgr.default_provider = provider
        elif mgr.clients:
            mgr.default_provider = list(mgr.clients.keys())[0]
        
        logger.info(f"LLM client initialized with provider={mgr.default_provider}, available={list(mgr.clients.keys())}")
    
    # Initialize memory manager
    get_memory_manager()
    logger.info("Memory manager initialized")
    
    # Initialize tool manager
    get_tool_manager()
    logger.info("Tool manager initialized")

    # Initialize task scheduler
    await initialize_task_scheduler()
    logger.info("Task scheduler initialized and started")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {AGENT_NAME}")
    await shutdown_task_scheduler()
    logger.info("Task scheduler shut down")

# Create FastAPI app
app = FastAPI(
    title=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    version=AGENT_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Returns the current health status of the application."""
    monitor.record_metric("health_check_requests", 1)
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": AGENT_VERSION,
        "agent_name": AGENT_NAME,
        "active_connections": len(ws_manager.active_connections)
    }

@app.post("/agent/chat", summary="Send a message to the agent and get a response")
async def chat_with_agent(request: AgentRequest, http_request: Request):
    """Processes a user message through the agentic loop and returns the final state."""
    monitor.record_metric("chat_requests", 1)
    
    client_ip = http_request.client.host
    allowed, info = rate_limiter.is_allowed(client_ip)
    if not allowed:
        security_auditor.log_event("rate_limit_exceeded", "medium", {"ip": client_ip})
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    
    is_valid, error_msg = input_validator.validate_string(request.user_message, max_length=5000)
    if not is_valid:
        security_auditor.log_event("invalid_input", "low", {"ip": client_ip, "error": error_msg})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error_msg}")

    try:
        orchestrator = get_orchestrator()
        conversation_id = request.conversation_id or str(uuid.uuid4())
        state = await orchestrator.run_agent_loop(
            conversation_id=conversation_id,
            user_message=request.user_message,
            context=request.context
        )
        monitor.record_metric("chat_success", 1 if state.success else 0)
        return state
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        monitor.record_metric("chat_errors", 1)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/agent/stream_chat", summary="Stream agent's response in real-time via SSE")
async def stream_chat_with_agent(request: AgentRequest, http_request: Request):
    """Streams the agent's thought process and final response using SSE."""
    monitor.record_metric("stream_chat_requests", 1)

    client_ip = http_request.client.host
    allowed, _ = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    async def event_generator():
        conversation_id = request.conversation_id or str(uuid.uuid4())
        orchestrator = get_orchestrator()
        
        try:
            yield f"event: status\ndata: {json.dumps({'status': 'started', 'conversation_id': conversation_id})}\n\n"
            
            state = await orchestrator.run_agent_loop(
                conversation_id=conversation_id,
                user_message=request.user_message,
                context=request.context
            )
            
            # Stream the response token by token for better UX
            if state.response:
                words = state.response.split(' ')
                for i, word in enumerate(words):
                    token = word + (' ' if i < len(words) - 1 else '')
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                    await asyncio.sleep(0.02)  # Small delay for streaming effect
            
            # Send final state
            yield f"event: result\ndata: {json.dumps(state.dict(), default=str)}\n\n"
            yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time bidirectional chat."""
    await ws_manager.connect(websocket, conversation_id)
    
    try:
        # Send welcome message
        await ws_manager.send_json(conversation_id, {
            "type": "connected",
            "conversation_id": conversation_id,
            "message": f"Connected to {AGENT_NAME} v{AGENT_VERSION}"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            
            if not user_message:
                continue
            
            # Validate input
            is_valid, error_msg = input_validator.validate_string(user_message, max_length=5000)
            if not is_valid:
                await ws_manager.send_json(conversation_id, {
                    "type": "error",
                    "error": f"Invalid input: {error_msg}"
                })
                continue
            
            # Send thinking status
            await ws_manager.send_json(conversation_id, {
                "type": "thinking",
                "message": "Agent is thinking..."
            })
            
            try:
                orchestrator = get_orchestrator()
                
                # Send progress updates
                await ws_manager.send_json(conversation_id, {
                    "type": "status",
                    "status": "processing",
                    "message": "Running agentic loop..."
                })
                
                state = await orchestrator.run_agent_loop(
                    conversation_id=conversation_id,
                    user_message=user_message
                )
                
                # Send thought process info
                if state.thought:
                    await ws_manager.send_json(conversation_id, {
                        "type": "thought",
                        "reasoning": state.thought.reasoning,
                        "plan": state.thought.plan,
                        "next_action": state.thought.next_action,
                        "confidence": state.thought.confidence
                    })
                
                # Send actions taken
                if state.actions:
                    await ws_manager.send_json(conversation_id, {
                        "type": "actions",
                        "actions": [
                            {
                                "type": a.type,
                                "description": a.description
                            } for a in state.actions
                        ]
                    })
                
                # Stream the final response
                if state.response:
                    # Stream token by token
                    words = state.response.split(' ')
                    for i, word in enumerate(words):
                        token = word + (' ' if i < len(words) - 1 else '')
                        await ws_manager.send_json(conversation_id, {
                            "type": "token",
                            "content": token
                        })
                        await asyncio.sleep(0.02)
                
                # Send complete signal
                await ws_manager.send_json(conversation_id, {
                    "type": "complete",
                    "success": state.success,
                    "iterations": state.iteration,
                    "conversation_id": conversation_id
                })
                
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await ws_manager.send_json(conversation_id, {
                    "type": "error",
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        ws_manager.disconnect(conversation_id)
        logger.info(f"WebSocket disconnected: {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(conversation_id)

@app.get("/metrics", summary="Get application metrics")
async def get_metrics():
    return monitor.get_metrics()

class LLMSettingsRequest(BaseModel):
    provider: str
    api_key: str
    model: str
    base_url: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    top_p: Optional[float] = 0.95

class AgentSettingsRequest(BaseModel):
    name: Optional[str] = "Manus Agent Pro"
    system_prompt: Optional[str] = None
    max_iterations: Optional[int] = 10
    enable_reflection: Optional[bool] = True
    enable_memory: Optional[bool] = True
    enable_web_browsing: Optional[bool] = True
    enable_file_ops: Optional[bool] = True
    enable_github: Optional[bool] = True

class SettingsRequest(BaseModel):
    llm: LLMSettingsRequest
    agent: Optional[AgentSettingsRequest] = None

# In-memory settings storage (persists during runtime)
_current_settings: Dict[str, Any] = {}

@app.post("/settings", summary="Update agent settings including LLM provider and system prompt")
async def update_settings(request: SettingsRequest):
    """Update agent settings dynamically at runtime."""
    global _current_settings
    
    try:
        from server.llm_client import get_llm_client, OpenAICompatibleClient
        import server.agent_config as agent_config
        
        llm = request.llm
        
        # Update LLM client
        mgr = get_llm_client()
        mgr.clients[llm.provider] = OpenAICompatibleClient(
            api_key=llm.api_key,
            base_url=llm.base_url,
            model=llm.model,
            provider=llm.provider
        )
        mgr.default_provider = llm.provider
        
        # Update agent config if provided
        if request.agent:
            ag = request.agent
            if ag.name:
                agent_config.AGENT_NAME = ag.name
            if ag.system_prompt:
                agent_config.SYSTEM_PROMPT = ag.system_prompt
        
        # Store settings
        _current_settings = {
            "llm": {
                "provider": llm.provider,
                "model": llm.model,
                "base_url": llm.base_url,
                "temperature": llm.temperature,
                "max_tokens": llm.max_tokens,
                "top_p": llm.top_p,
            },
            "agent": {
                "name": request.agent.name if request.agent else agent_config.AGENT_NAME,
                "max_iterations": request.agent.max_iterations if request.agent else 10,
            }
        }
        
        logger.info(f"Settings updated: provider={llm.provider}, model={llm.model}")
        return {"success": True, "message": f"Settings updated: {llm.provider}/{llm.model}"}
    
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/settings", summary="Get current agent settings")
async def get_settings():
    """Get current agent settings."""
    from server.llm_client import get_llm_client
    import server.agent_config as agent_config
    
    mgr = get_llm_client()
    return {
        "llm": {
            "provider": mgr.default_provider,
            "available_providers": list(mgr.clients.keys()),
        },
        "agent": {
            "name": agent_config.AGENT_NAME,
            "version": agent_config.AGENT_VERSION,
        },
        "custom": _current_settings
    }

@app.post("/settings/test", summary="Test LLM API connection")
async def test_llm_connection(request: LLMSettingsRequest):
    """Test if the provided LLM API key and settings are valid."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        response = await client.chat.completions.create(
            model=request.model,
            messages=[{"role": "user", "content": "Say 'OK' in one word."}],
            max_tokens=10,
            temperature=0.1
        )
        
        reply = response.choices[0].message.content
        return {
            "success": True,
            "message": f"Connected to {request.provider}/{request.model}. Response: {reply}",
            "provider": request.provider,
            "model": request.model
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": request.provider
        }

@app.get("/security/summary", summary="Get security audit summary")
async def get_security_summary():
    return security_auditor.get_security_summary()

@app.get("/conversations/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get conversation history for a given conversation ID."""
    try:
        memory = get_memory_manager()
        history = memory.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
