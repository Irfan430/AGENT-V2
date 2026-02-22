import asyncio
import logging
import json
import uuid
import os
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException, status
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info(f"Starting {AGENT_NAME} v{AGENT_VERSION}")
    
    # Initialize LLM client with the provided API key
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        logger.error("LLM_API_KEY not set. Agent will not function correctly.")
    else:
        initialize_llm_client(api_key=api_key)
        logger.info("LLM client initialized successfully")
    
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
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": AGENT_VERSION}

@app.post("/agent/chat", summary="Send a message to the agent and get a response")
async def chat_with_agent(request: AgentRequest, http_request: Request):
    """Processes a user message through the agentic loop and returns the final state."""
    monitor.record_metric("chat_requests", 1)
    
    # Security: Rate limiting
    client_ip = http_request.client.host
    allowed, info = rate_limiter.is_allowed(client_ip)
    if not allowed:
        security_auditor.log_event("rate_limit_exceeded", "medium", {"ip": client_ip})
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    
    # Security: Input validation
    is_valid, error_msg = input_validator.validate_string(request.user_message, max_length=5000)
    if not is_valid:
        security_auditor.log_event("invalid_input", "low", {"ip": client_ip, "error": error_msg})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid input: {error_msg}")

    try:
        orchestrator = get_orchestrator()
        state = await orchestrator.run_agent_loop(
            conversation_id=request.conversation_id or str(uuid.uuid4()),
            user_message=request.user_message,
            context=request.context
        )
        monitor.record_metric("chat_success", 1 if state.success else 0)
        return state
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        monitor.record_metric("chat_errors", 1)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.post("/agent/stream_chat", summary="Stream agent's response in real-time")
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
            
            # This is a simplified streaming implementation. 
            # In a real Manus-like system, the orchestrator would yield events during its loop.
            state = await orchestrator.run_agent_loop(
                conversation_id=conversation_id,
                user_message=request.user_message,
                context=request.context
            )
            
            # Send final state
            yield f"event: result\ndata: {json.dumps(state.dict(), default=str)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/metrics", summary="Get application metrics")
async def get_metrics():
    return monitor.get_metrics()

@app.get("/security/summary", summary="Get security audit summary")
async def get_security_summary():
    return security_auditor.get_security_summary()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
