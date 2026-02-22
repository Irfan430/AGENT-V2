"""
RAG (Retrieval-Augmented Generation) system for context-aware responses.
Combines memory retrieval with LLM generation for better answers.
"""

import logging
from typing import Optional, List, Dict, Any
from memory_manager_advanced import get_memory_manager
from llm_client import get_llm_client, Message
from agent_config import get_system_prompt

logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Retrieval-Augmented Generation system.
    Retrieves relevant context from memory and uses it to augment LLM responses.
    """
    
    def __init__(self):
        """Initialize the RAG system."""
        self.memory_manager = get_memory_manager()
        self.llm_client = get_llm_client()
        logger.info("RAG system initialized")
    
    async def generate_with_context(
        self,
        query: str,
        context_type: str = "memories",
        k: int = 5,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a response with retrieved context.
        
        Args:
            query: User query
            context_type: Type of context to retrieve
            k: Number of context items to retrieve
            temperature: LLM temperature
            
        Returns:
            Response with context and metadata
        """
        try:
            # Retrieve relevant context
            context_items = self.memory_manager.retrieve_relevant_context(
                query=query,
                k=k,
                collection_name=context_type
            )
            
            # Build context string
            context_str = self._format_context(context_items)
            
            # Build prompt with context
            system_prompt = get_system_prompt()
            if context_str:
                system_prompt += f"\n\nRelevant Context:\n{context_str}"
            
            # Generate response
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=query)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=temperature,
                max_tokens=2048
            )
            
            logger.info(f"Generated response with {len(context_items)} context items")
            
            return {
                "response": response.content,
                "context_items": context_items,
                "context_count": len(context_items),
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error in RAG generation: {str(e)}")
            return {
                "response": "",
                "context_items": [],
                "context_count": 0,
                "success": False,
                "error": str(e)
            }
    
    async def answer_question(
        self,
        question: str,
        search_type: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        Args:
            question: Question to answer
            search_type: Optional filter for memory type
            k: Number of context items
            
        Returns:
            Answer with supporting context
        """
        try:
            # Search for relevant memories
            if search_type:
                memories = self.memory_manager.search_memories(
                    query=question,
                    memory_type=search_type,
                    k=k
                )
            else:
                memories = self.memory_manager.retrieve_relevant_context(
                    query=question,
                    k=k,
                    collection_name="memories"
                )
            
            # Build context
            context_str = self._format_context(memories)
            
            # Build answer prompt
            answer_prompt = f"""Based on the following context, answer the question:

Context:
{context_str}

Question: {question}

Provide a comprehensive answer based on the context. If the context doesn't contain relevant information, say so."""
            
            # Generate answer
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=answer_prompt)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=0.5,
                max_tokens=1024
            )
            
            logger.info(f"Answered question with {len(memories)} supporting memories")
            
            return {
                "answer": response.content,
                "supporting_memories": memories,
                "memory_count": len(memories),
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "answer": "",
                "supporting_memories": [],
                "memory_count": 0,
                "success": False,
                "error": str(e)
            }
    
    async def summarize_conversation(
        self,
        conversation_id: str,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Summarize a conversation.
        
        Args:
            conversation_id: ID of the conversation
            max_length: Maximum summary length
            
        Returns:
            Conversation summary
        """
        try:
            # Retrieve conversation
            conversation_text = self.memory_manager.retrieve_conversation_context(
                conversation_id=conversation_id
            )
            
            if not conversation_text:
                return {
                    "summary": "",
                    "success": False,
                    "error": "Conversation not found"
                }
            
            # Generate summary
            summary_prompt = f"""Summarize the following conversation concisely in {max_length} characters or less:

{conversation_text}

Summary:"""
            
            messages = [
                Message(role="system", content="You are a helpful assistant that summarizes conversations."),
                Message(role="user", content=summary_prompt)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=0.5,
                max_tokens=256
            )
            
            logger.info(f"Summarized conversation {conversation_id}")
            
            return {
                "summary": response.content,
                "conversation_id": conversation_id,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error summarizing conversation: {str(e)}")
            return {
                "summary": "",
                "success": False,
                "error": str(e)
            }
    
    async def extract_insights(
        self,
        query: str,
        k: int = 10
    ) -> Dict[str, Any]:
        """
        Extract insights from relevant memories.
        
        Args:
            query: Query for insight extraction
            k: Number of memories to analyze
            
        Returns:
            Extracted insights
        """
        try:
            # Retrieve relevant memories
            memories = self.memory_manager.retrieve_relevant_context(
                query=query,
                k=k,
                collection_name="memories"
            )
            
            if not memories:
                return {
                    "insights": [],
                    "success": False,
                    "error": "No relevant memories found"
                }
            
            # Format context
            context_str = self._format_context(memories)
            
            # Extract insights
            insight_prompt = f"""Analyze the following information and extract key insights:

Information:
{context_str}

Please provide:
1. Main findings
2. Patterns or trends
3. Recommendations
4. Areas for further investigation"""
            
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=insight_prompt)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=0.6,
                max_tokens=1024
            )
            
            logger.info(f"Extracted insights from {len(memories)} memories")
            
            return {
                "insights": response.content,
                "memory_count": len(memories),
                "success": True
            }
        
        except Exception as e:
            logger.error(f"Error extracting insights: {str(e)}")
            return {
                "insights": "",
                "success": False,
                "error": str(e)
            }
    
    def _format_context(self, context_items: List[Dict[str, Any]]) -> str:
        """
        Format context items for inclusion in prompts.
        
        Args:
            context_items: List of context items
            
        Returns:
            Formatted context string
        """
        if not context_items:
            return "No relevant context found."
        
        formatted = []
        for i, item in enumerate(context_items, 1):
            content = item.get("content", "")
            relevance = item.get("relevance_score", 0)
            
            formatted.append(f"{i}. {content} (relevance: {relevance:.2f})")
        
        return "\n".join(formatted)

# Global RAG system instance
_rag_system: Optional[RAGSystem] = None

def get_rag_system() -> RAGSystem:
    """Get or create the global RAG system."""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system
