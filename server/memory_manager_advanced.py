"""
Advanced memory management system using ChromaDB for vector storage.
Implements RAG (Retrieval-Augmented Generation) for long-term memory.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("ChromaDB not installed. Install with: pip install chromadb")

logger = logging.getLogger(__name__)

class AdvancedMemoryManager:
    """
    Advanced memory management using ChromaDB.
    Stores and retrieves memories using vector embeddings.
    Implements RAG for context-aware responses.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the memory manager.
        
        Args:
            db_path: Path to ChromaDB database
        """
        if not CHROMA_AVAILABLE:
            logger.error("ChromaDB not available")
            self.client = None
            self.collections = {}
            return
        
        self.db_path = db_path or os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Create database directory if needed
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.db_path,
                anonymized_telemetry=False
            )
            self.client = chromadb.Client(settings)
            logger.info(f"ChromaDB initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            self.client = None
        
        self.collections: Dict[str, Any] = {}
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize default collections."""
        if not self.client:
            return
        
        try:
            # Conversation memory collection
            self.collections["conversations"] = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "Conversation history and context"}
            )
            
            # Long-term memory collection
            self.collections["memories"] = self.client.get_or_create_collection(
                name="memories",
                metadata={"description": "Long-term memories and facts"}
            )
            
            # Task history collection
            self.collections["tasks"] = self.client.get_or_create_collection(
                name="tasks",
                metadata={"description": "Task history and results"}
            )
            
            # Knowledge base collection
            self.collections["knowledge"] = self.client.get_or_create_collection(
                name="knowledge",
                metadata={"description": "Knowledge base and references"}
            )
            
            logger.info(f"Initialized {len(self.collections)} collections")
        
        except Exception as e:
            logger.error(f"Error initializing collections: {str(e)}")
    
    def store_conversation(self, conversation_id: str, messages: List[Dict[str, str]], 
                          metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store conversation in memory.
        
        Args:
            conversation_id: ID of the conversation
            messages: List of messages in the conversation
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self.client or "conversations" not in self.collections:
            return False
        
        try:
            collection = self.collections["conversations"]
            
            # Format conversation as text
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in messages
            ])
            
            # Prepare metadata
            meta = metadata or {}
            meta["conversation_id"] = conversation_id
            meta["timestamp"] = datetime.now().isoformat()
            meta["message_count"] = len(messages)
            
            # Store in collection
            collection.add(
                ids=[conversation_id],
                documents=[conversation_text],
                metadatas=[meta]
            )
            
            logger.info(f"Stored conversation {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing conversation: {str(e)}")
            return False
    
    def store_memory(self, text: str, memory_type: str = "general",
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a memory in the knowledge base.
        
        Args:
            text: Memory text
            memory_type: Type of memory (general, fact, procedure, etc.)
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self.client or "memories" not in self.collections:
            return False
        
        try:
            collection = self.collections["memories"]
            
            # Generate ID based on hash
            memory_id = f"mem_{hash(text) % 10**8}"
            
            # Prepare metadata
            meta = metadata or {}
            meta["type"] = memory_type
            meta["timestamp"] = datetime.now().isoformat()
            
            # Store in collection
            collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[meta]
            )
            
            logger.info(f"Stored memory: {memory_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return False
    
    def store_task_result(self, task_id: str, task_description: str, result: str,
                         success: bool, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store task result in memory.
        
        Args:
            task_id: Task ID
            task_description: Description of the task
            result: Task result/output
            success: Whether task succeeded
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        if not self.client or "tasks" not in self.collections:
            return False
        
        try:
            collection = self.collections["tasks"]
            
            # Format task result
            task_text = f"Task: {task_description}\nResult: {result}"
            
            # Prepare metadata
            meta = metadata or {}
            meta["task_id"] = task_id
            meta["success"] = success
            meta["timestamp"] = datetime.now().isoformat()
            
            # Store in collection
            collection.add(
                ids=[task_id],
                documents=[task_text],
                metadatas=[meta]
            )
            
            logger.info(f"Stored task result: {task_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error storing task result: {str(e)}")
            return False
    
    def retrieve_relevant_context(self, query: str, k: int = 5,
                                 collection_name: str = "memories") -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query using RAG.
        
        Args:
            query: Query string
            k: Number of results to retrieve
            collection_name: Collection to search
            
        Returns:
            List of relevant memories with metadata
        """
        if not self.client or collection_name not in self.collections:
            return []
        
        try:
            collection = self.collections[collection_name]
            
            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })
            
            logger.info(f"Retrieved {len(formatted_results)} results for query")
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def retrieve_conversation_context(self, conversation_id: str) -> Optional[str]:
        """
        Retrieve a specific conversation from memory.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Conversation text or None
        """
        if not self.client or "conversations" not in self.collections:
            return None
        
        try:
            collection = self.collections["conversations"]
            
            # Get the conversation
            results = collection.get(
                ids=[conversation_id]
            )
            
            if results and results["documents"]:
                return results["documents"][0]
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            return None
    
    def search_memories(self, query: str, memory_type: Optional[str] = None,
                       k: int = 5) -> List[Dict[str, Any]]:
        """
        Search memories by query and optional type filter.
        
        Args:
            query: Search query
            memory_type: Optional memory type filter
            k: Number of results
            
        Returns:
            List of matching memories
        """
        if not self.client or "memories" not in self.collections:
            return []
        
        try:
            collection = self.collections["memories"]
            
            # Build where filter if type is specified
            where_filter = None
            if memory_type:
                where_filter = {"type": memory_type}
            
            # Query the collection
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where_filter
            )
            
            # Format results
            formatted_results = []
            if results and results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "type": results["metadatas"][0][i].get("type") if results["metadatas"] else None,
                        "timestamp": results["metadatas"][0][i].get("timestamp") if results["metadatas"] else None,
                        "relevance_score": 1 - (results["distances"][0][i] if results["distances"] else 0)
                    })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection statistics
        """
        if not self.client or collection_name not in self.collections:
            return {}
        
        try:
            collection = self.collections[collection_name]
            count = collection.count()
            
            return {
                "collection": collection_name,
                "total_items": count,
                "metadata": collection.metadata
            }
        
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        stats = {}
        for collection_name in self.collections:
            stats[collection_name] = self.get_collection_stats(collection_name)
        return stats
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all items from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Success status
        """
        if not self.client or collection_name not in self.collections:
            return False
        
        try:
            collection = self.collections[collection_name]
            
            # Get all IDs and delete them
            all_items = collection.get()
            if all_items and all_items["ids"]:
                collection.delete(ids=all_items["ids"])
            
            logger.info(f"Cleared collection: {collection_name}")
            return True
        
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False
    
    def export_memories(self, output_path: str) -> bool:
        """
        Export all memories to a JSON file.
        
        Args:
            output_path: Path to export file
            
        Returns:
            Success status
        """
        try:
            export_data = {}
            
            for collection_name, collection in self.collections.items():
                all_items = collection.get()
                export_data[collection_name] = {
                    "items": all_items
                }
            
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported memories to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting memories: {str(e)}")
            return False

# Global memory manager instance
_memory_manager: Optional[AdvancedMemoryManager] = None

def get_memory_manager() -> AdvancedMemoryManager:
    """Get or create the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = AdvancedMemoryManager()
    return _memory_manager
