from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import os
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.services.memory_service import MemoryService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Perfect Partner API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Google Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class ChatMemory(BaseModel):
    text: str
    timestamp: Optional[str] = None
    relevance_score: Optional[float] = None

class RecommendationRequest(BaseModel):
    question: str

@app.post("/api/upload-chat")
async def upload_chat(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and process a chat history file
    """
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        memory_service = MemoryService(db)
        metadata = memory_service.process_and_store_chat(text)
        
        return {
            "message": "Chat history uploaded and processed successfully",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/get-recommendation")
async def get_recommendation(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a personalized recommendation based on chat context
    """
    try:
        memory_service = MemoryService(db)
        
        # Find relevant memories
        memories = memory_service.find_relevant_memories(request.question)
        
        if not memories:
            raise HTTPException(
                status_code=404,
                detail="No chat memories found. Please upload a chat history first."
            )
        
        # Generate recommendation
        result = memory_service.generate_recommendation(request.question, memories)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"} 