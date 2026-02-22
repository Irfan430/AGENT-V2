"""
Memory management system using ChromaDB for long-term memory and RAG.
Handles storing, retrieving, and managing agent memories.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Manages long-term memory using ChromaDB.
    Stores conversations, learned patterns, and contextual information.
    """
    
    def __init__(self, db_path: str = "./chroma_db"):
        """
        Initialize the memory manager.
        
        Args:
            db_path: Path to ChromaDB database directory
        """
        self.db_path = db_path
        
        # Create database directory if it doesn't exist
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB
        try:
            self.client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB initialized at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="agent_memory",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info("Memory collection initialized")
    
    def store(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Store text in memory.
        
        Args:
            text: Text to store
            metadata: Optional metadata about the text
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Document ID
        """
        try:
            # Generate ID if not provided
            if not doc_id:
                import uuid
                doc_id = str(uuid.uuid4())
            
            # Add timestamp to metadata
            if metadata is None:
                metadata = {}
            metadata["timestamp"] = datetime.now().isoformat()
            
            # Add to collection
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Stored memory with ID: {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            raise
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Retrieve similar memories based on a query.
        
        Args:
            query: Query text
            k: Number of results to return
            where: Optional filter conditions
            
        Returns:
            List of similar documents
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where
            )
            
            # Extract documents from results
            documents = results.get("documents", [[]])[0]
            
            logger.debug(f"Retrieved {len(documents)} memories for query")
            return documents
        
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return []
    
    def retrieve_with_metadata(
        self,
        query: str,
        k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar memories with metadata.
        
        Args:
            query: Query text
            k: Number of results to return
            where: Optional filter conditions
            
        Returns:
            List of documents with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where
            )
            
            # Combine documents with metadata
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            combined = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                combined.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": 1 - dist  # Convert distance to similarity
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
        Store a conversation exchange in memory.
        
        Args:
            conversation_id: ID of the conversation
            user_message: User's message
            agent_response: Agent's response
            metadata: Optional additional metadata
            
        Returns:
            Document ID
        """
        # Combine messages
        text = f"User: {user_message}\\nAgent: {agent_response}"
        
        # Add conversation metadata
        if metadata is None:
            metadata = {}
        metadata["conversation_id"] = conversation_id
        metadata["type"] = "conversation"
        
        return self.store(text, metadata=metadata)
    
    def store_learned_pattern(
        self,
        pattern: str,
        description: str,
        success_rate: float = 1.0
    ) -> str:
        """
        Store a learned pattern or strategy.
        
        Args:
            pattern: The pattern/strategy description
            description: Detailed description
            success_rate: Success rate of this pattern (0-1)
            
        Returns:
            Document ID
        """
        text = f"Pattern: {pattern}\\nDescription: {description}"
        metadata = {
            "type": "learned_pattern",
            "success_rate": success_rate
        }
        
        return self.store(text, metadata=metadata)
    
    def store_error_analysis(
        self,
        error_message: str,
        context: str,
        solution: str
    ) -> str:
        """
        Store an error and its solution for future reference.
        
        Args:
            error_message: The error message
            context: Context in which the error occurred
            solution: Solution that worked
            
        Returns:
            Document ID
        """
        text = f"Error: {error_message}\\nContext: {context}\\nSolution: {solution}"
        metadata = {
            "type": "error_analysis"
        }
        
        return self.store(text, metadata=metadata)
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            logger.debug(f"Deleted memory with ID: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return False
    
    def update(
        self,
        doc_id: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a memory.
        
        Args:
            doc_id: Document ID to update
            text: New text (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {}
            if text is not None:
                update_data["documents"] = [text]
            if metadata is not None:
                metadata["timestamp"] = datetime.now().isoformat()
                update_data["metadatas"] = [metadata]
            
            if update_data:
                self.collection.update(ids=[doc_id], **update_data)
                logger.debug(f"Updated memory with ID: {doc_id}")
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error updating memory: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory collection.
        
        Returns:
            Dictionary with statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_items": count
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"total_items": 0}
    
    def clear(self) -> bool:
        """
        Clear all memories.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all IDs
            all_items = self.collection.get()
            ids = all_items.get("ids", [])
            
            # Delete all
            if ids:
                self.collection.delete(ids=ids)
            
            logger.info("Cleared all memories")
            return True
        
        except Exception as e:
            logger.error(f"Error clearing memories: {str(e)}")
            return False
    
    def search_by_metadata(
        self,
        where: Dict[str, Any],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories by metadata.
        
        Args:
            where: Metadata filter conditions
            k: Maximum number of results
            
        Returns:
            List of matching documents with metadata
        """
        try:
            results = self.collection.get(
                where=where,
                limit=k
            )
            
            documents = results.get("documents", [])
            metadatas = results.get("metadatas", [])
            
            combined = []
            for doc, meta in zip(documents, metadatas):
                combined.append({
                    "text": doc,
                    "metadata": meta
                })
            
            return combined
        
        except Exception as e:
            logger.error(f"Error searching by metadata: {str(e)}")
            return []
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages from a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of conversation messages
        """
        return self.search_by_metadata(
            where={"conversation_id": conversation_id},
            k=100
        )
