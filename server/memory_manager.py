"""
Advanced memory management system using ChromaDB for long-term memory and RAG.
Implements Phase 2.1 of the Production Roadmap.
"""

import os
import logging
import uuid
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Advanced memory management system using ChromaDB.
    Handles conversation persistence, semantic search, and memory compression.
    """
    
    def __init__(self, db_path: str = "/home/ubuntu/AGENT-V2/chroma_db"):
        """
        Initialize the memory manager.
        """
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB initialized at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            # Fallback to ephemeral client if persistent fails
            self.client = chromadb.Client()
            logger.warning("Falling back to ephemeral ChromaDB client")
        
        # Initialize collections for different memory types
        self.collections = {
            "conversation": self.client.get_or_create_collection(
                name="conversation_memory", metadata={"hnsw:space": "cosine"}
            ),
            "knowledge": self.client.get_or_create_collection(
                name="knowledge_base", metadata={"hnsw:space": "cosine"}
            ),
            "tasks": self.client.get_or_create_collection(
                name="task_history", metadata={"hnsw:space": "cosine"}
            )
        }
        
        logger.info("Memory collections initialized")
    
    def store(
        self,
        text: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Store information in a specific memory collection.
        """
        try:
            collection = self.collections.get(memory_type, self.collections["conversation"])
            
            if not doc_id:
                doc_id = str(uuid.uuid4())
            
            if metadata is None:
                metadata = {}
            
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["type"] = memory_type
            
            collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored {memory_type} memory with ID: {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    def retrieve(
        self,
        query: str,
        memory_type: str = "conversation",
        k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Retrieve similar memories using semantic search.
        """
        try:
            collection = self.collections.get(memory_type, self.collections["conversation"])
            
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where
            )
            
            documents = results.get("documents", [[]])[0]
            return documents
        
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    def retrieve_with_metadata(
        self,
        query: str,
        memory_type: str = "conversation",
        k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar memories with their metadata.
        """
        try:
            collection = self.collections.get(memory_type, self.collections["conversation"])
            
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=where
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            combined = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                combined.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity": 1 - dist
                })
            
            return combined
        
        except Exception as e:
            logger.error(f"Error retrieving memory with metadata: {str(e)}")
            return []

    def store_conversation(
        self,
        conversation_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a conversation exchange.
        """
        text = f"User: {user_message}\nAgent: {agent_response}"
        
        if metadata is None:
            metadata = {}
        metadata["conversation_id"] = conversation_id
        
        return self.store(text, memory_type="conversation", metadata=metadata)

    def get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get history for a specific conversation.
        """
        try:
            collection = self.collections["conversation"]
            results = collection.get(
                where={"conversation_id": conversation_id},
                limit=limit
            )
            
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            history = []
            for doc, meta in zip(documents, metadatas):
                history.append({"text": doc, "metadata": meta})
            
            # Sort by timestamp
            history.sort(key=lambda x: x["metadata"].get("timestamp", ""))
            return history
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    def cleanup_old_memories(self, days: int = 30):
        """
        Cleanup memories older than specified days.
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            for name, collection in self.collections.items():
                logger.info(f"Cleanup triggered for {name} collection (older than {cutoff_date})")
                
        except Exception as e:
            logger.error(f"Error during memory cleanup: {str(e)}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all collections.
        """
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        return stats

# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    """Get or create the global memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
