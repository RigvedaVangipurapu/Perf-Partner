# Perfect Partner MVP

A hyper-personalized recommendation engine that analyzes chat histories to provide thoughtful, personalized suggestions for gifts, date nights, and more.

## Features

- Upload and analyze chat history files
- Convert conversations into meaningful memories
- Generate personalized recommendations based on chat context
- Private and secure - all data stored locally

## Tech Stack

- Backend: Python with FastAPI
- Frontend: Streamlit
- Database: SQLite (local storage)
- AI: Google Gemini API for recommendations

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
uvicorn app.main:app --reload
```

4. In a new terminal, start the Streamlit frontend:
```bash
streamlit run app.py
```

## Environment Variables

Create a `.env` file in the root directory with:
```
GOOGLE_API_KEY=your_gemini_api_key
```

## Project Structure

```
perfect-partner/
├── app/                    # Backend application
│   ├── main.py            # FastAPI application
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── app.py                 # Streamlit frontend
└── tests/                # Test files
``` 
