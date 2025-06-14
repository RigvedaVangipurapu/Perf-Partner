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
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("💝 Perfect Partner")
st.markdown("""
    Your AI-powered relationship assistant that helps you find the perfect gifts and date ideas
    based on your chat history with your partner.
""")

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

# File upload section
st.header("Step 1: Upload Chat History")
st.markdown("""
    Upload your chat history file (WhatsApp, iMessage, or other messenger exports).
    Your data stays private and is stored locally on your device.
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

# Recommendation section
if st.session_state.get('chat_uploaded', False):
    st.header("Step 2: Get Personalized Recommendations")
    
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
                        with st.expander("View Context Used"):
                            for memory in data['context_used']:
                                st.markdown(f"* {memory}")
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
        <p>Your data is stored locally and never leaves your device</p>
    </div>
""", unsafe_allow_html=True) 