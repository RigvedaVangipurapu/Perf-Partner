from typing import List, Dict
import json
import numpy as np
from sqlalchemy.orm import Session
from app.models.database import ChatMemory
from app.utils.chat_processor import ChatProcessor
import google.generativeai as genai
from datetime import datetime

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_processor = ChatProcessor()
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def process_and_store_chat(self, text: str) -> Dict:
        """
        Process chat history and store memories in the database
        """
        # Process the chat
        processed_data = self.chat_processor.process_chat(text)
        
        # Store chunks as memories
        for chunk in processed_data['chunks']:
            memory = ChatMemory(
                text=chunk,
                timestamp=datetime.utcnow(),  # TODO: Extract actual timestamp from chunk
                embedding=None,  # TODO: Generate and store embedding
                relevance_score=None
            )
            self.db.add(memory)
        
        self.db.commit()
        return processed_data['metadata']
    
    def find_relevant_memories(self, query: str, limit: int = 5) -> List[ChatMemory]:
        """
        Find the most relevant memories for a given query
        TODO: Implement proper semantic search using embeddings
        For now, return the most recent memories
        """
        return self.db.query(ChatMemory)\
            .order_by(ChatMemory.created_at.desc())\
            .limit(limit)\
            .all()
    
    def generate_recommendation(self, query: str, memories: List[ChatMemory]) -> Dict:
        """
        Generate a personalized recommendation using the Gemini model
        """
        # Prepare context from memories
        context = "\n".join([f"Memory: {memory.text}" for memory in memories])
        
        # Create prompt for Gemini
        prompt = f"""
        Based on the following chat memories:
        {context}
        
        Question: {query}
        
        Please provide a thoughtful, personalized recommendation that takes into account the specific details from the chat history.
        Focus on being specific and personal, referencing actual details from the conversations.
        """
        
        # Generate response
        response = self.model.generate_content(prompt)
        
        return {
            "recommendation": response.text,
            "context_used": [memory.text for memory in memories]
        } 