"""
FastAPI application for the Manus Agent Pro.
Handles API endpoints, WebSocket connections, and agent orchestration.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from agent_config import (
    AGENT_NAME,
    AGENT_VERSION,
    AGENT_DESCRIPTION,
    get_system_prompt
)
from llm_client import initialize_llm_client, get_llm_client, Message
from agent_state import AgentState, ConversationHistory, create_initial_state
from memory_manager import MemoryManager
from agent_orchestrator import get_orchestrator
from tool_manager import get_tool_manager
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
memory_manager: Optional[MemoryManager] = None
conversation_histories: dict = {}  # conversation_id -> ConversationHistory
orchestrator = None
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
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {AGENT_NAME}")

# Create FastAPI app
app = FastAPI(
    title=AGENT_NAME,
    description=AGENT_DESCRIPTION,
    version=AGENT_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    conversation_id: Optional[str] = None
    include_memory: bool = True

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    conversation_id: str
    response: str
    thinking: Optional[str] = None
    actions_taken: List[str] = []
    success: bool = True
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    agent_name: str
    version: str
    llm_available: bool
    memory_available: bool

# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check the health of the agent."""
    try:
        llm_client = get_llm_client()
        llm_available = llm_client is not None
    except:
        llm_available = False
    
    return HealthResponse(
        status="healthy",
        agent_name=AGENT_NAME,
        version=AGENT_VERSION,
        llm_available=llm_available,
        memory_available=memory_manager is not None
    )

@app.get("/info")
async def get_info():
    """Get information about the agent."""
    return {
        "name": AGENT_NAME,
        "version": AGENT_VERSION,
        "description": AGENT_DESCRIPTION,
        "system_prompt": get_system_prompt(),
        "capabilities": [
            "Terminal execution",
            "File operations",
            "Web browsing",
            "GitHub integration",
            "Image analysis",
            "Audio transcription",
            "Task scheduling",
            "Parallel execution",
            "Long-term memory",
            "Self-correction"
        ]
    }

# ============================================================================
# Chat Endpoints
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Process a user message and generate a response.
    
    Args:
        request: ChatRequest with user message
        background_tasks: FastAPI background tasks
        
    Returns:
        ChatResponse with agent's response
    """
    try:
        # Generate or use provided conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Get or create conversation history
        if conversation_id not in conversation_histories:
            conversation_histories[conversation_id] = ConversationHistory(
                conversation_id=conversation_id
            )
        
        history = conversation_histories[conversation_id]
        
        # Add user message to history
        history.add_message("user", request.message)
        
        # Get LLM client
        llm_client = get_llm_client()
        
        # Prepare messages for LLM
        system_message = Message(role="system", content=get_system_prompt())
        messages = [system_message]
        
        # Add memory context if requested
        if request.include_memory and memory_manager:
            relevant_memories = memory_manager.retrieve(request.message, k=3)
            if relevant_memories:
                memory_context = "\\n\\nRelevant memories:\\n" + "\\n".join(relevant_memories)
                messages.append(Message(role="system", content=memory_context))
        
        # Add conversation history
        for msg in history.messages[:-1]:  # Exclude the current message we just added
            messages.append(Message(role=msg.role, content=msg.content))
        
        # Add current user message
        messages.append(Message(role="user", content=request.message))
        
        # Get response from LLM
        logger.info(f"Processing message for conversation {conversation_id}")
        response = await llm_client.chat_completion_async(
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        # Add response to history
        history.add_message("assistant", response.content)
        
        # Store in memory for future reference
        if memory_manager:
            memory_manager.store(
                f"User: {request.message}\\nAgent: {response.content}",
                metadata={
                    "conversation_id": conversation_id,
                    "type": "conversation"
                }
            )
        
        logger.info(f"Successfully processed message for conversation {conversation_id}")
        
        return ChatResponse(
            conversation_id=conversation_id,
            response=response.content,
            success=True
        )
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return ChatResponse(
            conversation_id=request.conversation_id or "unknown",
            response="",
            success=False,
            error=str(e)
        )

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history."""
    if conversation_id not in conversation_histories:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    history = conversation_histories[conversation_id]
    return {
        "conversation_id": conversation_id,
        "messages": history.get_messages_for_llm(),
        "created_at": history.created_at.isoformat(),
        "updated_at": history.updated_at.isoformat()
    }

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in conversation_histories:
        del conversation_histories[conversation_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")

# ============================================================================
# WebSocket for Real-time Streaming
# ============================================================================

@app.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for real-time chat with streaming responses.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for conversation {conversation_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                await websocket.send_json({"error": "Empty message"})
                continue
            
            # Get or create conversation history
            if conversation_id not in conversation_histories:
                conversation_histories[conversation_id] = ConversationHistory(
                    conversation_id=conversation_id
                )
            
            history = conversation_histories[conversation_id]
            history.add_message("user", message)
            
            # Get LLM client
            llm_client = get_llm_client()
            
            # Prepare messages
            system_message = Message(role="system", content=get_system_prompt())
            messages = [system_message]
            
            # Add memory context
            if memory_manager:
                relevant_memories = memory_manager.retrieve(message, k=3)
                if relevant_memories:
                    memory_context = "\\n\\nRelevant memories:\\n" + "\\n".join(relevant_memories)
                    messages.append(Message(role="system", content=memory_context))
            
            # Add conversation history
            for msg in history.messages[:-1]:
                messages.append(Message(role=msg.role, content=msg.content))
            
            messages.append(Message(role="user", content=message))
            
            # Stream response
            full_response = ""
            try:
                async for chunk in llm_client.stream_chat_completion(messages=messages):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "token",
                        "content": chunk
                    })
                
                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "content": full_response
                })
                
                # Add to history
                history.add_message("assistant", full_response)
                
                # Store in memory
                if memory_manager:
                    memory_manager.store(
                        f"User: {message}\\nAgent: {full_response}",
                        metadata={
                            "conversation_id": conversation_id,
                            "type": "conversation"
                        }
                    )
            
            except Exception as e:
                logger.error(f"Error during streaming: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    finally:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")

# ============================================================================
# Memory Endpoints
# ============================================================================

@app.post("/api/memory/store")
async def store_memory(data: dict):
    """Store data in memory."""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    
    memory_manager.store(text, metadata=metadata)
    return {"status": "stored"}

@app.get("/api/memory/retrieve")
async def retrieve_memory(query: str, k: int = 5):
    """Retrieve similar items from memory."""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    results = memory_manager.retrieve(query, k=k)
    return {"results": results}

@app.get("/api/memory/stats")
async def memory_stats():
    """Get memory statistics."""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory manager not available")
    
    return {
        "total_items": memory_manager.get_stats()
    }

# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting {AGENT_NAME} on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
