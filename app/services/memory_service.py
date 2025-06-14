from typing import List, Dict
import json
import numpy as np
from sqlalchemy.orm import Session
from app.models.database import ChatMemory, PartnerNote, ChatFile, Person
from app.utils.chat_processor import ChatProcessor
import google.generativeai as genai
from datetime import datetime

class MemoryService:
    def __init__(self, db: Session):
        self.db = db
        self.chat_processor = ChatProcessor()
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def extract_people_with_llm(self, chat_text: str) -> list:
        """
        Use Gemini LLM to extract a list of real participant names from the chat transcript.
        Returns a list of names, or None if LLM fails.
        """
        prompt = (
            "Extract a list of all real participant names (not system messages or group actions) from the following chat transcript. "
            "Return only the names as a JSON array, e.g. [\"Alice\", \"Bob\"]. If you cannot find any, return an empty array: []. "
            "Do not return any explanation or text, only the JSON array.\n\n"
            f"Chat transcript:\n{chat_text[:12000]}"
        )
        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()
            print(f"[LLM People Extraction] Raw response: {raw}")
            # Remove code block markers if present
            if raw.startswith('```json'):
                raw = raw[len('```json'):].strip()
            if raw.startswith('```'):
                raw = raw[len('```'):].strip()
            if raw.endswith('```'):
                raw = raw[:-3].strip()
            import json as pyjson
            names = pyjson.loads(raw)
            if isinstance(names, list) and all(isinstance(n, str) for n in names):
                return names
        except Exception as e:
            print(f"⚠️ LLM people extraction failed: {e}. Raw response: {getattr(response, 'text', None)}")
        return None

    def process_and_store_chat(self, text: str, filename: str = None, file_size: int = None) -> Dict:
        """
        Process chat history and store memories in the database, linking each message to a Person
        """
        # Use LLM to extract people
        llm_people = self.extract_people_with_llm(text)
        if not llm_people:
            print("No people extracted by LLM. Skipping people creation.")
            participants = []
        else:
            participants = llm_people
        processed_data = self.chat_processor.process_chat(text)
        participant_map = {}  # name -> Person object

        # Create or update Person entries for each participant
        for name in participants:
            person = self.db.query(Person).filter(Person.name == name).first()
            if not person:
                person = Person(name=name, message_count=0)
                self.db.add(person)
                self.db.commit()
                self.db.refresh(person)
            participant_map[name] = person

        # Create chat file record
        chat_file = ChatFile(
            filename=filename or "unknown_file.txt",
            file_size=file_size,
            total_messages=processed_data['metadata']['total_messages'],
            participants=json.dumps(participants),
            date_range_start=datetime.fromisoformat(processed_data['metadata']['date_range']['start']) if processed_data['metadata']['date_range']['start'] else None,
            date_range_end=datetime.fromisoformat(processed_data['metadata']['date_range']['end']) if processed_data['metadata']['date_range']['end'] else None
        )
        self.db.add(chat_file)
        self.db.commit()
        self.db.refresh(chat_file)

        # Store chunks as memories linked to the chat file and person
        default_person_id = participant_map[participants[0]].id if participants else None
        for chunk in processed_data['chunks']:
            memory = ChatMemory(
                chat_file_id=chat_file.id,
                person_id=default_person_id,
                text=chunk,
                timestamp=datetime.utcnow(),  # TODO: Extract actual timestamp from chunk
                embedding=None,  # TODO: Generate and store embedding
                relevance_score=None
            )
            self.db.add(memory)
            # Increment message count for the person
            if default_person_id:
                participant_map[participants[0]].message_count += 1
        self.db.commit()

        # Add chat file info to metadata
        processed_data['metadata']['chat_file_id'] = chat_file.id
        processed_data['metadata']['uploaded_at'] = chat_file.uploaded_at.isoformat()

        return processed_data['metadata']
    
    def get_all_chat_files(self) -> List[ChatFile]:
        """
        Get all uploaded chat files
        """
        return self.db.query(ChatFile)\
            .order_by(ChatFile.uploaded_at.desc())\
            .all()
    
    def delete_chat_file(self, chat_file_id: int) -> bool:
        """
        Delete a chat file and all its associated memories
        """
        # First delete all memories associated with this chat file
        self.db.query(ChatMemory)\
            .filter(ChatMemory.chat_file_id == chat_file_id)\
            .delete()
        
        # Then delete the chat file record
        chat_file = self.db.query(ChatFile).filter(ChatFile.id == chat_file_id).first()
        if chat_file:
            self.db.delete(chat_file)
            self.db.commit()
            return True
        return False
    
    def get_chat_file_stats(self) -> Dict:
        """
        Get statistics about uploaded chat files
        """
        total_files = self.db.query(ChatFile).count()
        total_memories = self.db.query(ChatMemory).count()
        total_notes = self.db.query(PartnerNote).count()
        
        return {
            "total_chat_files": total_files,
            "total_memories": total_memories,
            "total_notes": total_notes
        }
    
    def add_partner_note(self, title: str, content: str, category: str = None) -> PartnerNote:
        """
        Add a new note about the partner
        """
        note = PartnerNote(
            title=title,
            content=content,
            category=category
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note
    
    def get_all_notes(self) -> List[PartnerNote]:
        """
        Get all partner notes
        """
        return self.db.query(PartnerNote)\
            .order_by(PartnerNote.updated_at.desc())\
            .all()
    
    def update_note(self, note_id: int, title: str = None, content: str = None, category: str = None) -> PartnerNote:
        """
        Update an existing note
        """
        note = self.db.query(PartnerNote).filter(PartnerNote.id == note_id).first()
        if note:
            if title:
                note.title = title
            if content:
                note.content = content
            if category:
                note.category = category
            note.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(note)
        return note
    
    def delete_note(self, note_id: int) -> bool:
        """
        Delete a note
        """
        note = self.db.query(PartnerNote).filter(PartnerNote.id == note_id).first()
        if note:
            self.db.delete(note)
            self.db.commit()
            return True
        return False
    
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
    
    def find_relevant_notes(self, query: str, limit: int = 3) -> List[PartnerNote]:
        """
        Find relevant notes based on query
        TODO: Implement proper search/matching
        For now, return recent notes
        """
        return self.db.query(PartnerNote)\
            .order_by(PartnerNote.updated_at.desc())\
            .limit(limit)\
            .all()
    
    def generate_recommendation(self, query: str, memories: List[ChatMemory] = None, notes: List[PartnerNote] = None) -> Dict:
        """
        Generate a personalized recommendation using the Gemini model
        """
        if memories is None:
            memories = self.find_relevant_memories(query)
        if notes is None:
            notes = self.find_relevant_notes(query)
        
        # Prepare context from memories and notes
        context_parts = []
        
        if memories:
            context_parts.append("Chat History Context:")
            for memory in memories:
                context_parts.append(f"- {memory.text}")
        
        if notes:
            context_parts.append("\nPersonal Notes About Partner:")
            for note in notes:
                context_parts.append(f"- {note.title}: {note.content}")
        
        context = "\n".join(context_parts)
        
        # Create prompt for Gemini
        prompt = f"""
        Based on the following information about this person and their relationship:
        
        {context}
        
        Question: {query}
        
        Please provide a thoughtful, personalized recommendation that takes into account the specific details from both the chat history and personal notes.
        Focus on being specific and personal, referencing actual details from the conversations and notes.
        """
        
        # Generate response
        response = self.model.generate_content(prompt)
        
        return {
            "recommendation": response.text,
            "context_used": {
                "chat_memories": [memory.text for memory in memories],
                "partner_notes": [f"{note.title}: {note.content}" for note in notes]
            }
        }
    
    def get_all_people(self) -> List[Dict]:
        """
        Get all people/profiles with at least 1 message (for debugging and small chats)
        """
        people = self.db.query(Person).filter(Person.message_count >= 1).order_by(Person.name.asc()).all()
        return [
            {
                "id": person.id,
                "name": person.name,
                "aliases": json.loads(person.aliases) if person.aliases else [],
                "first_message_date": person.first_message_date.isoformat() if person.first_message_date else None,
                "last_message_date": person.last_message_date.isoformat() if person.last_message_date else None,
                "message_count": person.message_count,
                "profile_notes": person.profile_notes
            }
            for person in people
        ] 