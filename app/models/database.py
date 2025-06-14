from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Create SQLite database in the user's home directory
db_path = os.path.expanduser("~/perfect_partner.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatFile(Base):
    __tablename__ = "chat_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    total_messages = Column(Integer, nullable=True)
    participants = Column(Text, nullable=True)  # JSON string of participant names
    date_range_start = Column(DateTime, nullable=True)
    date_range_end = Column(DateTime, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=False)
    aliases = Column(Text, nullable=True)  # JSON list of alternative names
    first_message_date = Column(DateTime, nullable=True)
    last_message_date = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    profile_notes = Column(Text, nullable=True)

class ChatMemory(Base):
    __tablename__ = "chat_memories"

    id = Column(Integer, primary_key=True, index=True)
    chat_file_id = Column(Integer, nullable=True)  # Reference to ChatFile
    person_id = Column(Integer, nullable=True)  # Reference to Person
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    embedding = Column(Text, nullable=True)  # Store embedding as JSON string
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class PartnerNote(Base):
    __tablename__ = "partner_notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "interests", "preferences", "memories"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def migrate_database():
    """
    Handle database migrations for schema changes
    """
    try:
        with engine.connect() as conn:
            # Check if chat_file_id and person_id columns exist in chat_memories table
            result = conn.execute(text("PRAGMA table_info(chat_memories)"))
            columns = [row[1] for row in result.fetchall()]
            if 'chat_file_id' not in columns:
                conn.execute(text("ALTER TABLE chat_memories ADD COLUMN chat_file_id INTEGER"))
                conn.commit()
                print("✅ Database migration: Added chat_file_id column to chat_memories table")
            if 'person_id' not in columns:
                conn.execute(text("ALTER TABLE chat_memories ADD COLUMN person_id INTEGER"))
                conn.commit()
                print("✅ Database migration: Added person_id column to chat_memories table")
            # Check if people table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='people'"))
            if not result.fetchone():
                # Create the people table
                Base.metadata.tables['people'].create(bind=engine)
                print("✅ Database migration: Created people table")
    except Exception as e:
        print(f"⚠️ Database migration warning: {e}")

# Create tables and run migrations
Base.metadata.create_all(bind=engine)
migrate_database()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 