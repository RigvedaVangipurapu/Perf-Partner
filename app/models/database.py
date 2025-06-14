from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
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

class ChatMemory(Base):
    __tablename__ = "chat_memories"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=True)
    embedding = Column(Text, nullable=True)  # Store embedding as JSON string
    relevance_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 