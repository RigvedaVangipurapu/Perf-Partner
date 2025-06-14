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
    page_title="MemoryWeave",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed"
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

# Custom CSS with MemoryWeave theme inspired by Finch
st.markdown("""
    <style>
    /* ========================================
       FONTS & GLOBAL STYLES
       ======================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Main container - Overall app background and layout */
    .main {
        padding: 1.5rem;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #fafbff 0%, #f0f4ff 100%);
        min-height: 100vh;
    }
    
    /* ========================================
       HEADER SECTION - Logo, Title, Tagline
       ======================================== */
    .main-header {
        text-align: center;
        padding: 3rem 2rem;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        border-radius: 2rem;
        margin-bottom: 2rem;
        color: white;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Header background effect - Subtle light overlay */
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at 30% 20%, rgba(255,255,255,0.2) 0%, transparent 50%);
    }
    
    /* App title - "MemoryWeave" */
    .main-title {
        font-size: 3.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        position: relative;
        z-index: 1;
        letter-spacing: -0.02em;
    }
    
    /* App tagline - "Weave memories into meaningful connections" */
    .main-tagline {
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.9;
        margin-bottom: 0;
        position: relative;
        z-index: 1;
        letter-spacing: 0.01em;
    }
    
    /* Logo icon - Thread emoji 🧵 */
    .logo-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        display: block;
        position: relative;
        z-index: 1;
    }
    
    /* ========================================
       TAB NAVIGATION - Upload, Manage, Notes, Recommendations
       ======================================== */
    /* Tab container - Glassmorphism background */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 1.5rem;
        padding: 0.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    /* Individual tab styling - Inactive state */
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0.75rem 1.5rem;
        border-radius: 1rem;
        font-weight: 500;
        border: none;
        background-color: transparent;
        color: #64748b;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 0.9rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Tab hover state - Purple tint and lift effect */
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.08);
        color: #6366f1;
        transform: translateY(-1px);
    }
    
    /* Active tab - Purple gradient background */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.25);
        transform: translateY(-2px);
    }
    
    /* Active tab hover - Darker purple gradient */
    .stTabs [aria-selected="true"]:hover {
        background: linear-gradient(135deg, #5b5ff0 0%, #8450f5 100%);
        color: white !important;
    }
    
    /* ========================================
       BUTTONS - Primary actions throughout the app
       ======================================== */
    /* Primary buttons - "Weave Memories", "Weave Note", etc. */
    .stButton>button {
        width: 100%;
        border-radius: 1rem;
        border: none;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        font-weight: 500;
        padding: 0.875rem 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        font-size: 0.95rem;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.2);
        position: relative;
        overflow: hidden;
    }
    
    /* Button shine effect - Animated light sweep */
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
        transition: left 0.6s ease;
    }
    
    /* Button hover state - Lift and enhanced shadow */
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        background: linear-gradient(135deg, #5b5ff0 0%, #8450f5 100%);
    }
    
    /* Button hover shine effect - Light sweep animation */
    .stButton>button:hover::before {
        left: 100%;
    }
    
    /* ========================================
       PRIVACY WARNING - Data usage notification
       ======================================== */
    .privacy-warning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #f59e0b;
        border-radius: 1.5rem;
        padding: 1.5rem;
        margin: 1.5rem 0;
        color: #92400e;
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.1);
        position: relative;
        backdrop-filter: blur(10px);
    }
    
    /* Privacy warning heading styling */
    .privacy-warning h4 {
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        color: #b91c1c !important;
    }
    
    /* ========================================
       CARDS - Memory files and personal notes display
       ======================================== */
    /* Card containers - Glassmorphism design */
    .note-card, .file-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 1.5rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    /* Card top border - Purple gradient line that appears on hover */
    .note-card::before, .file-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    
    /* Card hover state - Lift effect and enhanced shadow */
    .note-card:hover, .file-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.1);
        background: rgba(255, 255, 255, 0.95);
    }
    
    /* Card hover border effect - Top border appears */
    .note-card:hover::before, .file-card:hover::before {
        transform: scaleX(1);
    }
    
    /* Card titles - Note titles and file names */
    .note-title, .file-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.75rem;
        font-size: 1.1rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* File title specific styling - Purple color */
    .file-title {
        color: #6366f1;
    }
    
    /* Note category tags - "Interests", "Preferences", etc. */
    .note-category {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 2rem;
        font-size: 0.75rem;
        font-weight: 500;
        display: inline-block;
        margin-bottom: 0.75rem;
        font-family: 'Poppins', sans-serif;
    }
    
    /* File statistics - Message count, size, participants, dates */
    .file-stats {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.6;
        font-family: 'Inter', sans-serif;
    }
    
    /* ========================================
       STATS DASHBOARD - Memory tapestry overview
       ======================================== */
    .stats-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.9) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 2rem;
        padding: 2rem;
        margin: 1.5rem 0;
        text-align: center;
        box-shadow: 0 16px 48px rgba(99, 102, 241, 0.1);
        position: relative;
        overflow: hidden;
    }
    
    /* Stats card background animation - Floating effect */
    .stats-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
        animation: float 6s ease-in-out infinite;
    }
    
    /* Floating animation keyframes */
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-10px) rotate(180deg); }
    }
    
    /* Stats card heading - "Your Memory Tapestry" */
    .stats-card h4 {
        color: #6366f1;
        margin-bottom: 1rem;
        font-weight: 600;
        font-size: 1.3rem;
        position: relative;
        z-index: 1;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Stats card content - File counts and metrics */
    .stats-card p {
        position: relative;
        z-index: 1;
        font-size: 1rem;
        font-weight: 500;
        color: #475569;
        font-family: 'Inter', sans-serif;
    }
    
    /* ========================================
       INFO/WARNING BANNERS - e.g. reminders, alerts
       ======================================== */
    .stAlert, .stInfo, .stWarning, .stSuccess, .stError, .stNotification {
        background: linear-gradient(135deg, #fde8e8 0%, #fef2f2 100%) !important;
        border: 1.5px solid #fecaca !important;
        color: #b91c1c !important;
        border-radius: 1.2rem !important;
        box-shadow: 0 2px 12px rgba(239, 68, 68, 0.10) !important;
        font-family: 'Poppins', sans-serif !important;
    }
    .stAlert *, .stInfo *, .stWarning *, .stSuccess *, .stError *, .stNotification * {
        color: #b91c1c !important;
    }
    .stAlert h1, .stAlert h2, .stAlert h3, .stAlert h4, .stAlert h5, .stAlert h6,
    .stInfo h1, .stInfo h2, .stInfo h3, .stInfo h4, .stInfo h5, .stInfo h6,
    .stWarning h1, .stWarning h2, .stWarning h3, .stWarning h4, .stWarning h5, .stWarning h6,
    .stSuccess h1, .stSuccess h2, .stSuccess h3, .stSuccess h4, .stSuccess h5, .stSuccess h6,
    .stError h1, .stError h2, .stError h3, .stError h4, .stError h5, .stError h6,
    .stNotification h1, .stNotification h2, .stNotification h3, .stNotification h4, .stNotification h5, .stNotification h6 {
        color: #b91c1c !important;
        font-weight: 700;
    }
    
    /* ========================================
       FORM INPUTS - Text fields, textareas, selects
       ======================================== */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>select {
        border-radius: 1rem;
        border: 1.5px solid #d1c4e9;
        background: #f6f3ff !important;
        color: #1e293b !important;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.06);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    /* Placeholder/example text color for all inputs */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #8b8fa3 !important;
        opacity: 1 !important;
        font-style: italic;
    }
    
    /* Form input focus state - Purple border and enhanced background */
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus, .stSelectbox>div>div>select:focus {
        border-color: #a78bfa;
        box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.14);
        background: #fff !important;
        color: #1e293b !important;
    }
    
    /* ========================================
       DELETE BUTTONS - File and note removal
       ======================================== */
    .stButton>button[kind="secondary"] {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
        color: white;
        width: auto;
        padding: 0.5rem 1rem;
        font-size: 1.1rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 14px rgba(239, 68, 68, 0.2);
    }
    
    /* Delete button hover state - Darker red and lift effect */
    .stButton>button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(239, 68, 68, 0.3);
    }
    
    /* ========================================
       FOOTER - App branding and privacy info
       ======================================== */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #64748b;
        border-top: 1px solid rgba(226, 232, 240, 0.5);
        margin-top: 3rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Footer brand name - "MemoryWeave" */
    .footer-brand {
        font-weight: 600;
        color: #6366f1;
        font-family: 'Poppins', sans-serif;
    }
    
    /* ========================================
       TYPOGRAPHY - Section headers and text
       ======================================== */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: #1e293b;
        font-weight: 600;
    }
    
    /* ========================================
       ANIMATIONS - Page load and interactions
       ======================================== */
    /* Fade in animation for content sections */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Apply fade-in animation to main content */
    .main > div {
        animation: fadeInUp 0.6s ease-out;
    }

    /* Add CSS for recommendation output color */
    .recommendation-output {
        color: #1e293b !important;
        font-size: 1.08rem;
        font-family: 'Inter', sans-serif;
        line-height: 1.7;
    }

    /* ========================================
       MEMORY ANALYSIS CARD - Upload summary
       ======================================== */
    .memory-analysis-card {
        background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
        border: 2px solid #a5b4fc;
        border-radius: 1.5rem;
        padding: 2rem 1.5rem;
        margin: 2rem 0 1.5rem 0;
        color: #3730a3;
        box-shadow: 0 4px 24px rgba(99, 102, 241, 0.08);
        font-family: 'Poppins', sans-serif;
    }
    .memory-analysis-details {
        color: #6b7280;
        font-size: 1.05rem;
        font-family: 'Inter', sans-serif;
    }

    /* ========================================
       GLOBAL TEXT COLOR OVERRIDE
       ======================================== */
    body, .main, .file-card, .note-card, .stats-card, .memory-analysis-card, .memory-analysis-details, .recommendation-output, .footer, .stTabs [data-baseweb="tab"], .stButton>button, .file-title, .note-title, .file-stats, .note-category, .privacy-warning, .stAlert, .stInfo, .stWarning, .stSuccess, .stError, .stNotification {
        color: #1e293b !important;
    }
    /* For lighter/secondary text, use a medium grey */
    .file-stats, .memory-analysis-details, .footer, .note-category {
        color: #6b7280 !important;
    }
    /* For headings in cards/sections */
    .file-title, .note-title, .main-title, .main-tagline, .stats-card h4, .memory-analysis-card h3 {
        color: #3730a3 !important;
    }
    /* Remove any color: white from buttons, tabs, etc. */
    .stButton>button, .stTabs [data-baseweb="tab"] {
        color: #1e293b !important;
    }
    /* Ensure placeholder text is also not white */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #8b8fa3 !important;
        opacity: 1 !important;
        font-style: italic;
    }
    </style>
""", unsafe_allow_html=True)

# Header with new branding
st.markdown("""
    <div class="main-header">
        <div class="logo-icon">🧵</div>
        <h1 class="main-title">MemoryWeave</h1>
        <p class="main-tagline">Weave memories into meaningful connections</p>
    </div>
""", unsafe_allow_html=True)

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
# Add a new 'People' tab
people_tab, tab1, tab2, tab3, tab4 = st.tabs(["👤 People", "📁 Upload Memories", "🗂️ Manage Files", "📝 Personal Notes", "✨ Get Recommendations"])

with people_tab:
    st.header("People")
    st.markdown("""
        Automatically detected people from your chat histories. Each profile is built from the names found in your uploaded chats.
    """)
    try:
        response = requests.get('http://localhost:8000/api/people')
        if response.status_code == 200:
            people = response.json()
            if people:
                for person in people:
                    with st.container():
                        col1, col2 = st.columns([8, 1])
                        with col1:
                            st.markdown(f"""
                                <div class="file-card">
                                    <div class="file-title">👤 {person['name']}</div>
                                    <div class="file-stats">
                                        <b>Messages:</b> {person['message_count']}<br>
                                        <b>Aliases:</b> {', '.join(person['aliases']) if person['aliases'] else '—'}<br>
                                        <b>First Message:</b> {person['first_message_date'] or '—'}<br>
                                        <b>Last Message:</b> {person['last_message_date'] or '—'}<br>
                                        <b>Profile Notes:</b> {person['profile_notes'] or '—'}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_person_{person['id']}", help="Delete person"):
                                try:
                                    delete_response = requests.delete(f'http://localhost:8000/api/people/{person["id"]}')
                                    if delete_response.status_code == 200:
                                        st.success("Person deleted!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Error deleting person")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No people detected yet. Upload a chat file to get started!")
        else:
            st.error("Error loading people profiles.")
    except Exception as e:
        st.error(f"Error loading people: {str(e)}")

with tab1:
    st.header("Upload Your Memories")
    st.markdown("""
        Upload your chat history files to start weaving your memories into meaningful connections.
        Support for WhatsApp, iMessage, and other messenger exports.
    """)

    uploaded_file = st.file_uploader("Choose a chat history file", type=['txt'], help="Upload your exported chat files here")

    if uploaded_file is not None:
        if st.button("🧵 Weave Memories", type="primary"):
            with st.spinner("Weaving your memories into the tapestry..."):
                try:
                    # Send file to backend
                    files = {'file': uploaded_file}
                    response = requests.post('http://localhost:8000/api/upload-chat', files=files, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['chat_uploaded'] = True
                        st.session_state['metadata'] = data['metadata']
                        st.session_state['files_refresh'] += 1
                        st.success("✨ Memories successfully woven into your tapestry!")
                        
                        # Display metadata
                        st.markdown("""
                            <div class="memory-analysis-card">
                                <h3>🧠 Memory Analysis</h3>
                                <div class="memory-analysis-details">
                        """, unsafe_allow_html=True)
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
                        st.markdown("""
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error(f"Error weaving memories: {response.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The server might be busy. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.header("Manage Your Memory Files")
    st.markdown("""
        View and manage your uploaded memory files. Each file represents a thread in your tapestry of connections.
    """)
    
    # Display stats
    try:
        stats_response = requests.get('http://localhost:8000/api/stats')
        if stats_response.status_code == 200:
            stats = stats_response.json()
            st.markdown(f"""
                <div class="stats-card">
                    <h4>🧵 Your Memory Tapestry</h4>
                    <p><strong>{stats['total_chat_files']}</strong> Memory Files | 
                    <strong>{stats['total_memories']}</strong> Woven Memories | 
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
                st.subheader("Your Memory Files")
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
                                        <small>Woven: {file['uploaded_at'].split('T')[0]}</small>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_file_{file['id']}", help="Remove from tapestry"):
                                try:
                                    delete_response = requests.delete(f'http://localhost:8000/api/chat-files/{file["id"]}')
                                    if delete_response.status_code == 200:
                                        st.success("Memory file removed from tapestry!")
                                        st.session_state['files_refresh'] += 1
                                        st.rerun()
                                    else:
                                        st.error("Error removing file")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No memory files yet. Upload your first file in the 'Upload Memories' tab to start weaving your tapestry!")
        else:
            st.error("Error loading memory files")
    except Exception as e:
        st.error(f"Error loading memory files: {str(e)}")

with tab3:
    st.header("Personal Notes")
    st.markdown("""
        Add personal notes that will be woven into your recommendations. 
        These threads of insight help create richer, more meaningful connections.
    """)
    
    # Add new note section
    st.subheader("Add New Note")
    with st.form("add_note_form"):
        note_title = st.text_input("Title", placeholder="e.g., Favorite Restaurant, Birthday Preferences")
        note_content = st.text_area("Content", placeholder="Describe the details that matter...")
        note_category = st.selectbox("Category (Optional)", 
                                   ["", "Interests", "Preferences", "Memories", "Gifts", "Food", "Travel", "Other"])
        
        if st.form_submit_button("🧵 Weave Note", type="primary"):
            if note_title and note_content:
                try:
                    response = requests.post('http://localhost:8000/api/notes', 
                                           json={
                                               "title": note_title,
                                               "content": note_content,
                                               "category": note_category if note_category else None
                                           })
                    if response.status_code == 200:
                        st.success("✨ Note woven into your tapestry!")
                        st.session_state['notes_refresh'] += 1
                        st.rerun()
                    else:
                        st.error(f"Error weaving note: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please fill in both title and content.")
    
    # Display existing notes
    st.subheader("Your Woven Notes")
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
                                    <small style="color: #6c757d;">Woven: {note['created_at'][:10]}</small>
                                </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("🗑️", key=f"delete_note_{note['id']}", help="Remove note"):
                                try:
                                    delete_response = requests.delete(f'http://localhost:8000/api/notes/{note["id"]}')
                                    if delete_response.status_code == 200:
                                        st.success("Note removed!")
                                        st.rerun()
                                    else:
                                        st.error("Error removing note")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No notes woven yet. Add your first note above to start building your tapestry of insights!")
        else:
            st.error("Error loading notes")
    except Exception as e:
        st.error(f"Error loading notes: {str(e)}")

with tab4:
    st.header("Get Woven Recommendations")
    
    # Additional privacy reminder for recommendations
    st.info("🔔 **Reminder:** When you request a recommendation, relevant memories and notes will be sent to Google Gemini for AI processing.")
    
    # Question input
    question = st.text_input(
        "What would you like to know?",
        placeholder="e.g., What should I get for their birthday? or Suggest a meaningful date idea"
    )
    
    if st.button("✨ Weave Recommendation", type="primary"):
        if question:
            with st.spinner("Weaving your memories into a personalized recommendation..."):
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
                        st.subheader("Your Woven Recommendation")
                        st.markdown(f'<div class="recommendation-output">{data["recommendation"]}</div>', unsafe_allow_html=True)
                        
                        # Display context used
                        with st.expander("View Memory Threads Used (This data was sent to Google Gemini)"):
                            st.warning("The following memory threads were woven together for your recommendation:")
                            
                            if data['context_used']['chat_memories']:
                                st.markdown("**Memory Excerpts:**")
                                for memory in data['context_used']['chat_memories']:
                                    st.markdown(f"🧵 {memory}")
                            
                            if data['context_used']['partner_notes']:
                                st.markdown("**Personal Notes:**")
                                for note in data['context_used']['partner_notes']:
                                    st.markdown(f"📝 {note}")
                    else:
                        st.error(f"Error weaving recommendation: {response.text}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. The server might be busy. Please try again.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to the server. Please make sure the backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question first.")

# Footer
st.markdown("""
    <div class="footer">
        <p>Made with ❤️ by <span class="footer-brand">MemoryWeave</span></p>
        <p><strong>Privacy:</strong> Your memories and notes are stored locally. Recommendations require sending data to Google Gemini.</p>
    </div>
""", unsafe_allow_html=True) 