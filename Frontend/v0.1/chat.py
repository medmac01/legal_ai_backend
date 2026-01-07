import streamlit as st
import requests
import time
import os
import json
from tempfile import NamedTemporaryFile

# Set page configuration with light theme
st.set_page_config(
    page_title="PAKTON",
    page_icon="📜",
    layout="centered"
)

# Define supported MIME types
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain'
}

# Apply light theme and custom styling
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #262730; }
    h1 { color: #1E3A8A; font-family: 'Arial', sans-serif; font-weight: 700; padding-bottom: 1rem; }
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    .stChatMessage[data-testid="stChatMessageUser"] { background-color: #EFF6FF; border-left: 5px solid #3B82F6; }
    .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: #F0FDF4; border-left: 5px solid #10B981; }
    .custom-divider { height: 3px; background: #000000; border-radius: 3px; margin: 1rem 0; }
    .stChatInputContainer { padding-top: 1rem; }
    .footer { text-align: center; color: #6B7280; padding-top: 2rem; font-size: 0.8rem; }
    #MainMenu, footer, header, .viewerBadge_container__1QSob, .stDeployButton { display: none !important; }
    .tooltip { position: relative; display: inline-block; cursor: help; }
    .tooltip .tooltiptext {
        visibility: hidden; width: 300px; background-color: #F0FDF4; color: #262730;
        text-align: left; border-radius: 6px; border: 1px solid #10B981; padding: 10px;
        position: absolute; z-index: 1; bottom: 125%; left: 50%; margin-left: -150px;
        opacity: 0; transition: opacity 0.3s; font-size: 14px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
    .tooltip .tooltiptext::after {
        content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px;
        border-width: 5px; border-style: solid;
        border-color: #10B981 transparent transparent transparent;
    }
</style>
""", unsafe_allow_html=True)

BASE_URL = "http://localhost:5001"
TERMINAL_STATUSES = ["SUCCESS", "FAILURE"]

def index_document(file_path: str):
    print("################# Request to /index/document/ endpoint ####################")
    url = f"{BASE_URL}/index/document/"
    file_extension = os.path.splitext(file_path)[1].lower()
    mime_type = MIME_TYPES.get(file_extension, 'application/octet-stream')
    metadata = {"title": "Test Document", "author": "Test Author"}

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, mime_type)}
        data = {"metadata": json.dumps(metadata)}
        response = requests.post(url, files=files, data=data)

    print(f"Endpoint's Response: {response.json()}")
    return response.json().get("data", {}).get("task_id")

def poll_task_status(task_id, initial_interval=2, max_retries=20, backoff_factor=1.5):
    current_interval = initial_interval
    url = f"{BASE_URL}/task_status/{task_id}"

    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            status = data.get("data", {}).get("task_status")
            if status in TERMINAL_STATUSES:
                return data
            time.sleep(current_interval)
            current_interval *= backoff_factor
        except requests.exceptions.RequestException as e:
            return {"error": f"Polling failed: {str(e)}"}

    return {"error": "Task polling timed out"}

def interrogation(userQuery, userContext="", userInstructions=""):
    url = f"{BASE_URL}/interrogation/"
    payload = {
        "userQuery": userQuery,
        "userContext": userContext,
        "userInstructions": userInstructions
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("task_id")
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to server: {e}")
        return None

def extract_response_text(response):
    if "error" in response:
        raise Exception(response["error"])
    task_status = response.get("data", {}).get("task_status")
    task_response = response.get("data", {}).get("task_response", {})
    if task_status != "SUCCESS" or task_response.get("status") != "SUCCESS":
        raise Exception(f"Task failed: {task_status}, details: {task_response.get('status')}")
    return task_response.get("data", {}).get("report", "No conclusion provided")

# Session state management
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_submitted_question" not in st.session_state:
    st.session_state.user_submitted_question = False
if "document_uploaded" not in st.session_state:
    st.session_state.document_uploaded = False
if "document_indexed" not in st.session_state:
    st.session_state.document_indexed = False
if "welcomed" not in st.session_state:
    st.session_state.welcomed = True

# App header
st.markdown("""
<h1 style='text-align: center; font-family: "Times New Roman", serif; font-weight: 700; letter-spacing: 5px; text-transform: uppercase; color: #000; margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1); padding-bottom: 10px;'>
   📜 PAKTON
</h1>
""", unsafe_allow_html=True)

st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>A Multi-Agent Framework <br> for Contract Document Analysis</h3>", unsafe_allow_html=True)
st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### About 📜 PAKTON")
    st.markdown("""
    PAKTON is a multi-agent framework for contract document analysis.
    
    ### The Agents
    - **Archivist**: Indexes and stores documents.
    - **Legal Researcher**: Answers questions based on documents.
    - **Legal Interrogator**: Breaks down user queries and interacts with the Researcher.

    ### Features
    - Document analysis and indexing
    - Legal Q&A
    - Precedent lookup
    - Term extraction
    """)
    with st.expander("How to use"):
        st.markdown("""
        1. Upload a contract file
        2. Ask your legal question
        3. Receive analysis with references
        """)

# Require document upload
if not st.session_state.document_uploaded:
    uploaded_file = st.file_uploader("Upload a contract file (.pdf, .docx, .txt) before proceeding:", type=["pdf", "docx", "txt"])
    if uploaded_file:
        with st.spinner("Uploading and indexing your document..."):
            try:
                suffix = os.path.splitext(uploaded_file.name)[1]
                with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(uploaded_file.read())
                    temp_file_path = temp_file.name
                task_id = index_document(temp_file_path)
                response = poll_task_status(task_id)
                task_status = response.get("data", {}).get("task_status")
                task_response = response.get("data", {}).get("task_response")
                if task_status == "SUCCESS" and task_response.get("status") == "SUCCESS":
                    st.session_state.document_uploaded = True
                    st.session_state.document_indexed = True
                    st.success("✅ Document indexed successfully. You may now ask your legal question.")
                else:
                    st.error(f"❌ Indexing failed. Status: {task_status}")
            except Exception as e:
                st.error(f"❌ Failed to index document: {str(e)}")
else:
    st.success("✅ Document already indexed.")

# Initial welcome message
if st.session_state.welcomed:
    with st.chat_message("assistant", avatar="🧑‍💼"):
        st.markdown("""
        👋 Hello I am the Legal Interrogator.

        I can answer any questions you have regarding the document of the EU AI act. <span class="tooltip">ℹ️
            <span class="tooltiptext">
                <strong>Instructions:</strong><br>
                1. Ask a specific legal question related to the EU AI Act.<br>
                2. Be precise for better results.<br>
                3. Analysis may take a moment.<br>
                4. One question per session.
            </span>
        </span>
        """, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": "👋 Hello I am the Legal Interrogator.\n\nI can answer any questions you have regarding the document of the EU AI act."})
        st.session_state.welcomed = False

# Chat UI
for idx, msg in enumerate(st.session_state.messages):
    icon = "👤" if msg["role"] == "user" else "🧑‍💼"
    with st.chat_message(msg["role"], avatar=icon):
        if msg["role"] == "assistant" and idx == 0:
            st.markdown(f"""
            <div>
                {msg["content"]}
                <span class="tooltip">ℹ️
                    <span class="tooltiptext">
                        <strong>Instructions:</strong><br>
                        1. Ask a specific legal question related to the EU AI Act.<br>
                        2. Be precise for better results.<br>
                        3. The analysis may take a moment.<br>
                        4. One question per session.
                    </span>
                </span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(msg["content"])

# Chat input
if st.session_state.document_indexed and not st.session_state.user_submitted_question:
    user_input = st.chat_input("Type your legal question here...")
    if user_input:
        st.session_state.user_submitted_question = True
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="🧑‍💼"):
            loading_placeholder = st.empty()
            with loading_placeholder:
                with st.spinner("Analyzing your question..."):
                    try:
                        task_id = interrogation(userQuery=user_input)
                        if task_id:
                            time.sleep(0.5)
                            with st.spinner("Analyzing the document..."):
                                result = poll_task_status(task_id)
                                response_text = extract_response_text(result)
                        else:
                            response_text = "❌ Failed to connect to the server. Please try again later."
                    except Exception as e:
                        response_text = f"❌ Error: {str(e)}"

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()
elif not st.session_state.document_indexed:
    st.info("Please upload and index a document before asking a question.")
else:
    st.info("You've already submitted your question. Only one question can be processed per session.")

# Footer
st.markdown("<div class='footer'>© 2025 PAKTON | Powered by Raptopoulos Petros | petrosrapto@gmail.com</div>", unsafe_allow_html=True)
