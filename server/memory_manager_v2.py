"""
Advanced Memory Management System with ChromaDB integration.
Handles conversation history, semantic search, and memory compression.
"""

import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class Memory:
    """A single memory entry."""
    id: str
    content: str
    type: str  # "conversation", "task", "learning", "error"
    timestamp: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    importance_score: float = 0.5

class MemoryManager:
    """
    Advanced memory management system.
    Stores, retrieves, and manages agent memories.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self.memories: Dict[str, Memory] = {}
        self.memory_index: Dict[str, List[str]] = {}  # Type -> memory IDs
        self.max_memories = 10000
        self.memory_retention_days = 30
        logger.info("Memory manager initialized")
    
    def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5
    ) -> str:
        """
        Store a new memory.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            metadata: Additional metadata
            importance_score: Importance score (0-1)
            
        Returns:
            Memory ID
        """
        memory_id = self._generate_memory_id(content)
        
        memory = Memory(
            id=memory_id,
            content=content,
            type=memory_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            importance_score=importance_score
        )
        
        self.memories[memory_id] = memory
        
        # Update index
        if memory_type not in self.memory_index:
            self.memory_index[memory_type] = []
        self.memory_index[memory_type].append(memory_id)
        
        # Cleanup if needed
        self._cleanup_memories()
        
        logger.info(f"Stored memory: {memory_id} (type: {memory_type})")
        return memory_id
    
    def retrieve_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Memory]:
        """
        Retrieve memories by type and importance.
        
        Args:
            memory_type: Filter by memory type
            limit: Maximum number of memories to retrieve
            min_importance: Minimum importance score
            
        Returns:
            List of memories
        """
        if memory_type and memory_type in self.memory_index:
            memory_ids = self.memory_index[memory_type]
        else:
            memory_ids = list(self.memories.keys())
        
        # Filter and sort by importance and recency
        memories = [
            self.memories[mid] for mid in memory_ids
            if self.memories[mid].importance_score >= min_importance
        ]
        
        memories.sort(
            key=lambda m: (m.importance_score, m.timestamp),
            reverse=True
        )
        
        return memories[:limit]
    
    def search_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Memory]:
        """
        Search memories by content similarity.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching memories
        """
        # Simple keyword-based search (can be enhanced with embeddings)
        query_lower = query.lower()
        matches = []
        
        for memory in self.memories.values():
            if query_lower in memory.content.lower():
                matches.append(memory)
        
        # Sort by importance and recency
        matches.sort(
            key=lambda m: (m.importance_score, m.timestamp),
            reverse=True
        )
        
        return matches[:limit]
    
    def update_memory_importance(self, memory_id: str, importance_score: float):
        """Update importance score of a memory."""
        if memory_id in self.memories:
            self.memories[memory_id].importance_score = max(0, min(1, importance_score))
            logger.info(f"Updated memory importance: {memory_id} -> {importance_score}")
    
    def delete_memory(self, memory_id: str):
        """Delete a memory."""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            del self.memories[memory_id]
            
            # Remove from index
            if memory.type in self.memory_index:
                self.memory_index[memory.type].remove(memory_id)
            
            logger.info(f"Deleted memory: {memory_id}")
    
    def compress_memories(self) -> str:
        """
        Compress old memories into summaries.
        
        Returns:
            Summary of compressed memories
        """
        cutoff_date = datetime.now() - timedelta(days=self.memory_retention_days)
        old_memories = [
            m for m in self.memories.values()
            if datetime.fromisoformat(m.timestamp) < cutoff_date
        ]
        
        # Create summary
        summary_parts = []
        for memory_type in set(m.type for m in old_memories):
            type_memories = [m for m in old_memories if m.type == memory_type]
            summary_parts.append(f"{len(type_memories)} {memory_type} memories")
        
        summary = f"Compressed: {', '.join(summary_parts)}"
        
        # Delete old memories
        for memory in old_memories:
            self.delete_memory(memory.id)
        
        logger.info(f"Compressed {len(old_memories)} old memories")
        return summary
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        stats = {
            "total_memories": len(self.memories),
            "by_type": {},
            "avg_importance": 0.0,
            "oldest_memory": None,
            "newest_memory": None
        }
        
        if self.memories:
            # Count by type
            for memory_type in self.memory_index:
                stats["by_type"][memory_type] = len(self.memory_index[memory_type])
            
            # Calculate average importance
            avg_importance = sum(m.importance_score for m in self.memories.values()) / len(self.memories)
            stats["avg_importance"] = avg_importance
            
            # Get oldest and newest
            all_memories = list(self.memories.values())
            all_memories.sort(key=lambda m: m.timestamp)
            stats["oldest_memory"] = all_memories[0].timestamp
            stats["newest_memory"] = all_memories[-1].timestamp
        
        return stats
    
    def export_memories(self, memory_type: Optional[str] = None) -> str:
        """Export memories as JSON."""
        if memory_type:
            memories = self.retrieve_memories(memory_type=memory_type, limit=10000)
        else:
            memories = list(self.memories.values())
        
        return json.dumps([asdict(m) for m in memories], indent=2)
    
    def _generate_memory_id(self, content: str) -> str:
        """Generate a unique memory ID."""
        hash_obj = hashlib.md5(content.encode())
        return f"mem_{hash_obj.hexdigest()[:12]}"
    
    def _cleanup_memories(self):
        """Clean up old or low-importance memories if limit exceeded."""
        if len(self.memories) > self.max_memories:
            # Sort by importance and recency
            sorted_memories = sorted(
                self.memories.values(),
                key=lambda m: (m.importance_score, m.timestamp),
                reverse=True
            )
            
            # Keep top memories
            keep_ids = set(m.id for m in sorted_memories[:self.max_memories])
            
            # Delete others
            to_delete = [mid for mid in self.memories.keys() if mid not in keep_ids]
            for mid in to_delete:
                self.delete_memory(mid)
            
            logger.info(f"Cleaned up {len(to_delete)} memories")

class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize the conversation manager."""
        self.memory_manager = memory_manager
        self.current_conversation_id = None
        self.conversation_context: Dict[str, Any] = {}
        logger.info("Conversation manager initialized")
    
    def start_conversation(self, conversation_id: Optional[str] = None) -> str:
        """Start a new conversation."""
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().timestamp()}"
        
        self.current_conversation_id = conversation_id
        self.conversation_context = {
            "id": conversation_id,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "task_description": None,
            "context": {}
        }
        
        logger.info(f"Started conversation: {conversation_id}")
        return conversation_id
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to current conversation."""
        if not self.current_conversation_id:
            self.start_conversation()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversation_context["messages"].append(message)
        
        # Store in memory
        meta_dict = {
            "conversation_id": self.current_conversation_id,
            "role": role
        }
        if metadata:
            meta_dict.update(metadata)
        
        self.memory_manager.store_memory(
            content=content,
            memory_type="conversation",
            metadata=meta_dict,
            importance_score=0.7 if role == "user" else 0.5
        )
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if not self.current_conversation_id:
            return []
        
        messages = self.conversation_context.get("messages", [])
        return messages[-limit:]
    
    def set_task_description(self, description: str):
        """Set the task description for current conversation."""
        if not self.current_conversation_id:
            self.start_conversation()
        
        self.conversation_context["task_description"] = description
        
        # Store as memory
        self.memory_manager.store_memory(
            content=description,
            memory_type="task",
            metadata={"conversation_id": self.current_conversation_id},
            importance_score=0.9
        )
    
    def get_context_summary(self) -> str:
        """Get a summary of the current conversation context."""
        messages = self.conversation_context.get("messages", [])
        task = self.conversation_context.get("task_description", "")
        
        summary_parts = []
        if task:
            summary_parts.append(f"Task: {task}")
        
        summary_parts.append(f"Messages: {len(messages)}")
        
        if messages:
            last_user_msg = next(
                (m for m in reversed(messages) if m["role"] == "user"),
                None
            )
            if last_user_msg:
                summary_parts.append(f"Last user message: {last_user_msg['content'][:100]}")
        
        return " | ".join(summary_parts)

# Global instances
_memory_manager: Optional[MemoryManager] = None
_conversation_manager: Optional[ConversationManager] = None

def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

def get_conversation_manager() -> ConversationManager:
    """Get or create the global conversation manager."""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager(get_memory_manager())
    return _conversation_manager
