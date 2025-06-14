import re
from typing import List, Dict
import pandas as pd
from datetime import datetime

class ChatProcessor:
    def __init__(self):
        self.timestamp_patterns = [
            r'\[\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?\s[AP]M\]',  # WhatsApp style
            r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}(?::\d{2})?\s[AP]M',       # Alternative format
            r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}',                            # ISO format
        ]
        
    def clean_text(self, text: str) -> str:
        """
        Remove system messages, timestamps, and clean up the text
        """
        # Remove timestamps
        for pattern in self.timestamp_patterns:
            text = re.sub(pattern, '', text)
        
        # Remove system messages (e.g., "Messages and calls are end-to-end encrypted")
        system_messages = [
            "Messages and calls are end-to-end encrypted",
            "You changed the group description",
            "You changed the group icon",
            "You added",
            "You removed",
            "You left",
            "You joined",
        ]
        
        for message in system_messages:
            text = text.replace(message, '')
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def split_into_chunks(self, text: str, max_chunk_size: int = 1000) -> List[str]:
        """
        Split the chat history into meaningful chunks
        """
        # Split by double newlines first (common in chat exports)
        messages = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for message in messages:
            message = message.strip()
            if not message:
                continue
                
            message_size = len(message)
            
            if current_size + message_size > max_chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            current_chunk.append(message)
            current_size += message_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def extract_metadata(self, text: str) -> Dict:
        """
        Extract metadata from chat messages
        """
        metadata = {
            'total_messages': 0,
            'date_range': {
                'start': None,
                'end': None
            },
            'participants': set()
        }
        
        # Count messages
        messages = text.split('\n')
        metadata['total_messages'] = len([m for m in messages if m.strip()])
        
        # Extract dates and participants
        for message in messages:
            # Extract dates
            for pattern in self.timestamp_patterns:
                match = re.search(pattern, message)
                if match:
                    date_str = match.group(0)
                    try:
                        date = datetime.strptime(date_str, '%m/%d/%Y, %I:%M:%S %p')
                        if not metadata['date_range']['start'] or date < metadata['date_range']['start']:
                            metadata['date_range']['start'] = date
                        if not metadata['date_range']['end'] or date > metadata['date_range']['end']:
                            metadata['date_range']['end'] = date
                    except ValueError:
                        continue
            
            # Extract participants (assuming format: "Name: Message")
            match = re.match(r'^([^:]+):', message)
            if match:
                participant = match.group(1).strip()
                metadata['participants'].add(participant)
        
        metadata['participants'] = list(metadata['participants'])
        return metadata
    
    def process_chat(self, text: str) -> Dict:
        """
        Process the entire chat history
        """
        cleaned_text = self.clean_text(text)
        chunks = self.split_into_chunks(cleaned_text)
        metadata = self.extract_metadata(text)
        
        return {
            'chunks': chunks,
            'metadata': metadata
        } 