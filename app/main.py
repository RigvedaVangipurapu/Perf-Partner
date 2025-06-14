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

class NoteRequest(BaseModel):
    title: str
    content: str
    category: Optional[str] = None

class NoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

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
        metadata = memory_service.process_and_store_chat(
            text=text,
            filename=file.filename,
            file_size=len(content)
        )
        
        return {
            "message": "Chat history uploaded and processed successfully",
            "metadata": metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat-files")
async def get_chat_files(db: Session = Depends(get_db)):
    """
    Get all uploaded chat files
    """
    try:
        memory_service = MemoryService(db)
        chat_files = memory_service.get_all_chat_files()
        
        return [
            {
                "id": file.id,
                "filename": file.filename,
                "file_size": file.file_size,
                "total_messages": file.total_messages,
                "participants": file.participants,
                "date_range_start": file.date_range_start.isoformat() if file.date_range_start else None,
                "date_range_end": file.date_range_end.isoformat() if file.date_range_end else None,
                "uploaded_at": file.uploaded_at.isoformat()
            }
            for file in chat_files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chat-files/{file_id}")
async def delete_chat_file(file_id: int, db: Session = Depends(get_db)):
    """
    Delete a chat file and all its associated memories
    """
    try:
        memory_service = MemoryService(db)
        success = memory_service.delete_chat_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat file not found")
        
        return {"message": "Chat file and associated memories deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the stored data
    """
    try:
        memory_service = MemoryService(db)
        stats = memory_service.get_chat_file_stats()
        return stats
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
        
        # Find relevant memories and notes
        memories = memory_service.find_relevant_memories(request.question)
        notes = memory_service.find_relevant_notes(request.question)
        
        if not memories and not notes:
            raise HTTPException(
                status_code=404,
                detail="No chat memories or notes found. Please upload a chat history or add some notes first."
            )
        
        # Generate recommendation
        result = memory_service.generate_recommendation(request.question, memories, notes)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notes")
async def create_note(note: NoteRequest, db: Session = Depends(get_db)):
    try:
        memory_service = MemoryService(db)
        created_note = memory_service.add_partner_note(
            title=note.title,
            content=note.content,
            category=note.category
        )
        return {
            "id": created_note.id,
            "title": created_note.title,
            "content": created_note.content,
            "category": created_note.category,
            "created_at": created_note.created_at,
            "updated_at": created_note.updated_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/notes")
async def get_notes(db: Session = Depends(get_db)):
    try:
        memory_service = MemoryService(db)
        notes = memory_service.get_all_notes()
        return [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "category": note.category,
                "created_at": note.created_at,
                "updated_at": note.updated_at
            }
            for note in notes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/notes/{note_id}")
async def update_note(note_id: int, note_update: NoteUpdateRequest, db: Session = Depends(get_db)):
    try:
        memory_service = MemoryService(db)
        updated_note = memory_service.update_note(
            note_id=note_id,
            title=note_update.title,
            content=note_update.content,
            category=note_update.category
        )
        if not updated_note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {
            "id": updated_note.id,
            "title": updated_note.title,
            "content": updated_note.content,
            "category": updated_note.category,
            "created_at": updated_note.created_at,
            "updated_at": updated_note.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    try:
        memory_service = MemoryService(db)
        success = memory_service.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return {"message": "Note deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 