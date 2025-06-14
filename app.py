import streamlit as st
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure the page
st.set_page_config(
    page_title="Perfect Partner",
    page_icon="💝",
    layout="wide"
)

# Initialize session state
if 'chat_uploaded' not in st.session_state:
    st.session_state['chat_uploaded'] = False
if 'metadata' not in st.session_state:
    st.session_state['metadata'] = None
if 'notes_refresh' not in st.session_state:
    st.session_state['notes_refresh'] = 0
if 'files_refresh' not in st.session_state:
    st.session_state['files_refresh'] = 0

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #475063;
    }
    .privacy-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .note-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .note-title {
        font-weight: bold;
        color: #495057;
        margin-bottom: 0.5rem;
    }
    .note-category {
        background-color: #e9ecef;
        color: #6c757d;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .file-card {
        background-color: #f1f3f4;
        border: 1px solid #dadce0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .file-title {
        font-weight: bold;
        color: #1a73e8;
        margin-bottom: 0.5rem;
    }
    .file-stats {
        color: #5f6368;
        font-size: 0.9rem;
    }
    .stats-card {
        background-color: #e8f0fe;
        border: 1px solid #1a73e8;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("💝 Perfect Partner")
st.markdown("""
    Your AI-powered relationship assistant that helps you find the perfect gifts and date ideas
    based on your chat history and personal notes about your partner.
""")

# Privacy Notice
st.markdown("""
    <div class="privacy-warning">
        <h4>🔒 Privacy Notice</h4>
        <p><strong>Important:</strong> When you request recommendations, relevant portions of your chat history and notes will be sent to Google Gemini AI for processing. While your data is stored locally on your device, the recommendation feature requires sending context to Google's servers.</p>
        <p>Please ensure you're comfortable with this before uploading sensitive conversations or adding personal notes.</p>
    </div>
""", unsafe_allow_html=True)

# Check if backend is running
def check_backend():
    try:
        response = requests.get('http://localhost:8000/api/health', timeout=2)
        return response.status_code == 200
    except:
        return False

if not check_backend():
    st.error("""
        ⚠️ Backend server is not running. Please start it first:
        1. Open a new terminal
        2. Run: `uvicorn app.main:app --reload`
    """)
    st.stop()

# Helper function to format file size
def format_file_size(size_bytes):
    if size_bytes is None:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["📁 Upload Chat", "🗂️ Manage Files", "📝 Partner Notes", "💡 Get Recommendations"])

with tab1:
    st.header("Upload Chat History")
    st.markdown("""
        Upload your chat history file (WhatsApp, iMessage, or other messenger exports).
        Your data is stored locally on your device.
    """)

    uploaded_file = st.file_uploader("Choose a chat history file", type=['txt'])

    if uploaded_file is not None:
        if st.button("Process Chat History"):
            with st.spinner("Processing your chat history..."):
                try:
                    # Send file to backend
                    files = {'file': uploaded_file}
                    response = requests.post('http://localhost:8000/api/upload-chat', files=files, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['chat_uploaded'] = True
                        st.session_state['metadata'] = data['metadata']
                        st.session_state['files_refresh'] += 1
                        st.success("Chat history processed successfully!")
                        
                        # Display metadata
                        st.subheader("Chat Analysis")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Messages", st.session_state['metadata']['total_messages'])
                            if st.session_state['metadata']['date_range']['start']:
                                st.write("Date Range:", 
                                       st.session_state['metadata']['date_range']['start'].split('T')[0],
                                       "to",
                                       st.session_state['metadata']['date_range']['end'].split('T')[0])
                        with col2:
                            st.write("Participants:", ", ".join(st.session_state['metadata']['participants']))
                    else:
                        st.error(f"Error processing chat history: {response.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The server might be busy. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.header("Manage Chat Files")
    st.markdown("""
        View and manage your uploaded chat history files. You can see details about each file
        and delete files you no longer need.
    """)
    
    # Display stats
    try:
        stats_response = requests.get('http://localhost:8000/api/stats')
        if stats_response.status_code == 200:
            stats = stats_response.json()
            st.markdown(f"""
                <div class="stats-card">
                    <h4>📊 Your Data Summary</h4>
                    <p><strong>{stats['total_chat_files']}</strong> Chat Files | 
                    <strong>{stats['total_memories']}</strong> Chat Memories | 
                    <strong>{stats['total_notes']}</strong> Personal Notes</p>
                </div>
            """, unsafe_allow_html=True)
    except:
        pass
    
    # Display uploaded files
    try:
        response = requests.get('http://localhost:8000/api/chat-files')
        if response.status_code == 200:
            chat_files = response.json()
            if chat_files:
                st.subheader("Your Uploaded Files")
                for file in chat_files:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            participants = json.loads(file['participants']) if file['participants'] else []
                            date_range = ""
                            if file['date_range_start'] and file['date_range_end']:
                                start_date = file['date_range_start'].split('T')[0]
                                end_date = file['date_range_end'].split('T')[0]
                                date_range = f"📅 {start_date} to {end_date}"
                            
                            st.markdown(f"""
                                <div class="file-card">
                                    <div class="file-title">📄 {file['filename']}</div>
                                    <div class="file-stats">
                                        💬 {file['total_messages']} messages | 
                                        📦 {format_file_size(file['file_size'])} | 
                                        👥 {', '.join(participants)}<br>
                                        {date_range}<br>
                                        <small>Uploaded: {file['uploaded_at'].split('T')[0]}</small>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_file_{file['id']}", help="Delete chat file"):
                                try:
                                    delete_response = requests.delete(f'http://localhost:8000/api/chat-files/{file["id"]}')
                                    if delete_response.status_code == 200:
                                        st.success("Chat file deleted!")
                                        st.session_state['files_refresh'] += 1
                                        st.rerun()
                                    else:
                                        st.error("Error deleting file")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No chat files uploaded yet. Upload your first file in the 'Upload Chat' tab!")
        else:
            st.error("Error loading chat files")
    except Exception as e:
        st.error(f"Error loading chat files: {str(e)}")

with tab3:
    st.header("Partner Notes")
    st.markdown("""
        Add personal notes about your partner that will help generate better recommendations.
        These could be preferences, interests, memories, or anything important to remember.
    """)
    
    # Add new note section
    st.subheader("Add New Note")
    with st.form("add_note_form"):
        note_title = st.text_input("Title", placeholder="e.g., Favorite Restaurant, Birthday Preferences")
        note_content = st.text_area("Content", placeholder="Describe the details...")
        note_category = st.selectbox("Category (Optional)", 
                                   ["", "Interests", "Preferences", "Memories", "Gifts", "Food", "Travel", "Other"])
        
        if st.form_submit_button("Add Note"):
            if note_title and note_content:
                try:
                    response = requests.post('http://localhost:8000/api/notes', 
                                           json={
                                               "title": note_title,
                                               "content": note_content,
                                               "category": note_category if note_category else None
                                           })
                    if response.status_code == 200:
                        st.success("Note added successfully!")
                        st.session_state['notes_refresh'] += 1
                        st.rerun()
                    else:
                        st.error(f"Error adding note: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please fill in both title and content.")
    
    # Display existing notes
    st.subheader("Your Notes")
    try:
        response = requests.get('http://localhost:8000/api/notes')
        if response.status_code == 200:
            notes = response.json()
            if notes:
                for note in notes:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"""
                                <div class="note-card">
                                    <div class="note-title">{note['title']}</div>
                                    {f'<div class="note-category">{note["category"]}</div>' if note['category'] else ''}
                                    <div>{note['content']}</div>
                                    <small style="color: #6c757d;">Added: {note['created_at'][:10]}</small>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_note_{note['id']}", help="Delete note"):
                                try:
                                    delete_response = requests.delete(f'http://localhost:8000/api/notes/{note["id"]}')
                                    if delete_response.status_code == 200:
                                        st.success("Note deleted!")
                                        st.rerun()
                                    else:
                                        st.error("Error deleting note")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No notes added yet. Add your first note above!")
        else:
            st.error("Error loading notes")
    except Exception as e:
        st.error(f"Error loading notes: {str(e)}")

with tab4:
    st.header("Get Personalized Recommendations")
    
    # Additional privacy reminder for recommendations
    st.info("🔔 **Reminder:** When you request a recommendation, relevant chat excerpts and notes will be sent to Google Gemini for AI processing.")
    
    # Question input
    question = st.text_input(
        "What would you like to know?",
        placeholder="e.g., What should I get for their birthday? or Suggest a date night idea"
    )
    
    if st.button("Get Recommendation"):
        if question:
            with st.spinner("Generating personalized recommendation..."):
                try:
                    # Send question to backend
                    response = requests.post(
                        'http://localhost:8000/api/get-recommendation',
                        json={'question': question},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Display recommendation
                        st.subheader("Your Personalized Recommendation")
                        st.markdown(data['recommendation'])
                        
                        # Display context used
                        with st.expander("View Context Used (This data was sent to Google Gemini)"):
                            st.warning("The following information was sent to Google Gemini for processing:")
                            
                            if data['context_used']['chat_memories']:
                                st.markdown("**Chat History Excerpts:**")
                                for memory in data['context_used']['chat_memories']:
                                    st.markdown(f"* {memory}")
                            
                            if data['context_used']['partner_notes']:
                                st.markdown("**Partner Notes:**")
                                for note in data['context_used']['partner_notes']:
                                    st.markdown(f"* {note}")
                    else:
                        st.error(f"Error getting recommendation: {response.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The server might be busy. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question first.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Made with ❤️ for better relationships</p>
        <p><strong>Privacy:</strong> Your chat files and notes are stored locally. Recommendations require sending data to Google Gemini.</p>
    </div>
""", unsafe_allow_html=True) 