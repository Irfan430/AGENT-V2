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
from server.agent_state import AgentState, ConversationHistory
from server.llm_client import get_llm_client, Message, initialize_llm_client
from server.monitoring import get_monitor
from server.security import RateLimiter, InputValidator
from server.agent_config import AGENT_NAME, AGENT_VERSION, AGENT_DESCRIPTION, get_system_prompt
from server.tool_manager import get_tool_manager
from server.task_scheduler import initialize_task_scheduler, shutdown_task_scheduler

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AGENT-V2 API",
    description="API for interacting with the production-grade AGENT-V2",
    version="2.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator = None
monitor = get_monitor()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60) # 10 requests per minute
input_validator = InputValidator()
memory_manager = None
tool_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info(f"Starting {AGENT_NAME} v{AGENT_VERSION}")
    
    # Initialize LLM client
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        logger.warning("LLM_API_KEY not set. Agent will not be able to make LLM calls.")
    else:
        initialize_llm_client(api_key=api_key)
        logger.info("LLM client initialized successfully")
    
    # Initialize memory manager
    from server.memory_manager import MemoryManager # Import here to avoid circular dependency
    global memory_manager
    memory_manager = MemoryManager()
    logger.info("Memory manager initialized")
    
    # Initialize orchestrator
    global orchestrator
    orchestrator = get_orchestrator()
    logger.info("Agent orchestrator initialized")
    
    # Initialize tool manager
    global tool_manager
    tool_manager = get_tool_manager()
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

class AgentRequest(BaseModel):
    user_message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Returns the current health status of the application."""
    monitor.record_metric("health_check_requests", 1)
    try:
        llm_client = get_llm_client()
        llm_available = llm_client is not None
    except:
        llm_available = False
    
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "llm_available": llm_available}

@app.post("/agent/chat", summary="Send a message to the agent and get a response")
async def chat_with_agent(request: AgentRequest, http_request: Request):
    """Processes a user message through the agentic loop and returns the final state."""
    monitor.record_metric("chat_requests", 1)
    
    # Input validation (Phase 7)
    is_valid, error_msg = input_validator.validate_string(request.user_message, max_length=2000)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid user message: {error_msg}")
    
    # Rate limiting (Phase 7)
    if not rate_limiter.is_allowed(http_request.client.host)[0]:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    try:
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
    """Streams the agent's thought process and final response using Server-Sent Events (SSE)."""
    monitor.record_metric("stream_chat_requests", 1)

    # Input validation (Phase 7)
    is_valid, error_msg = input_validator.validate_string(request.user_message, max_length=2000)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid user message: {error_msg}")

    # Rate limiting (Phase 7)
    if not rate_limiter.is_allowed(http_request.client.host)[0]:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    async def event_generator():
        conversation_id = request.conversation_id or str(uuid.uuid4())
        try:
            yield f"event: status\ndata: {json.dumps({'status': 'thinking', 'message': 'Agent is processing your request...' })}\n\n"
            await asyncio.sleep(0.1) # Small delay to ensure client receives status

            state = await orchestrator.run_agent_loop(
                conversation_id=conversation_id,
                user_message=request.user_message,
                context=request.context
            )
            
            if state.success:
                yield f"event: status\ndata: {json.dumps({'status': 'completed', 'message': 'Agent has completed the task.' })}\n\n"
                yield f"event: final_response\ndata: {json.dumps({'response': state.response, 'conversation_id': conversation_id })}\n\n"
            else:
                yield f"event: status\ndata: {json.dumps({'status': 'failed', 'message': 'Agent failed to complete the task.' })}\n\n"
                yield f"event: error\ndata: {json.dumps({'error': state.response or 'Unknown error', 'conversation_id': conversation_id })}\n\n"
            monitor.record_metric("stream_chat_success", 1 if state.success else 0)

        except asyncio.CancelledError:
            logger.warning("Client disconnected during stream_chat.")
            monitor.record_metric("stream_chat_cancelled", 1)
        except Exception as e:
            logger.error(f"Error in stream_chat_with_agent: {str(e)}")
            monitor.record_metric("stream_chat_errors", 1)
            yield f"event: error\ndata: {json.dumps({'error': str(e), 'conversation_id': conversation_id })}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/agent/status/{conversation_id}", summary="Get current status of an agent conversation")
async def get_agent_status(conversation_id: str):
    """Retrieves the current state and history of a specific agent conversation."""
    monitor.record_metric("status_requests", 1)
    # This would ideally fetch the state from a persistent store
    # For now, we'll return a placeholder or last known state if available
    return JSONResponse({"conversation_id": conversation_id, "status": "in_progress", "last_update": datetime.now().isoformat()})

@app.get("/metrics", summary="Get application metrics")
async def get_metrics():
    """Returns current application metrics for monitoring."""
    return monitor.get_metrics()

@app.get("/errors", summary="Get recent errors")
async def get_errors():
    """Returns recent errors recorded by the error handler."""
    return orchestrator.error_handler.get_recent_errors()

@app.get("/tasks", summary="Get scheduled tasks")
async def get_scheduled_tasks():
    """Returns all currently scheduled tasks."""
    from server.task_scheduler import get_task_scheduler
    scheduler = get_task_scheduler()
    return scheduler.get_all_tasks()

@app.get("/memory/stats", summary="Get memory statistics")
async def get_memory_stats():
    """Returns statistics about the memory manager."""
    from server.memory_manager import get_memory_manager
    memory_manager_instance = get_memory_manager()
    return memory_manager_instance.get_stats()


# Example of how to integrate a tool directly into an endpoint if needed
@app.post("/tool/execute_command", summary="Execute a shell command via API")
async def execute_shell_command(command_data: Dict[str, Any], http_request: Request):
    """Executes a shell command and returns the output."""
    monitor.record_metric("tool_execute_command_requests", 1)
    
    # Input validation (Phase 7)
    command = command_data.get("command", "")
    is_valid, error_msg = input_validator.validate_command(command)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid command: {error_msg}")

    # Rate limiting (Phase 7)
    if not rate_limiter.is_allowed(http_request.client.host)[0]:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    tool_manager_instance = get_tool_manager()
    result = await tool_manager_instance.execute_tool("execute_command", command_data, user_approved=True)
    if result["success"]:
        return JSONResponse({"output": result["result"]})
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"])

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting {AGENT_NAME} on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
