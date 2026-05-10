"""
Chat page for the Streamlit application.
"""

import streamlit as st
from utils.api_client import query_backend, document_upload_rag

# -------------------------------
# AUTH CHECK
# -------------------------------
if "user" not in st.session_state:
    st.warning("Please login first")
    st.switch_page("home.py")

user = st.session_state["user"]

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="LangGraph Chat", layout="wide")

st.title("💬 LangGraph Chat")
st.success(f"Logged in as {user.get('email')}")

# -------------------------------
# LOGOUT
# -------------------------------
if st.button("🔒 Logout"):
    st.session_state.clear()
    st.switch_page("home.py")

# -------------------------------
# DOCUMENT UPLOAD
# -------------------------------
with st.sidebar:
    st.header("📂 Upload Documents")

    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    file_description = st.text_input("Describe your document (optional)")

    if uploaded_file:
        file_key = uploaded_file.name

        if "uploaded_files" not in st.session_state:
            st.session_state.uploaded_files = {}

        if not file_description:
            file_description = "No description"

        if file_key not in st.session_state.uploaded_files:
            success = document_upload_rag(uploaded_file, file_description)

            if success:
                st.success(f"Uploaded: {uploaded_file.name}")
                st.session_state.uploaded_files[file_key] = True
            else:
                st.error(f"Upload failed: {uploaded_file.name}")
        else:
            st.info(f"Already uploaded: {uploaded_file.name}")

# -------------------------------
# CHAT
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("Ask a question...")

if user_input:
    st.session_state.chat_history.append(("user", user_input))

    response = query_backend(user_input, user.get("email"))

    st.session_state.chat_history.append(("assistant", response))
    st.rerun()

# -------------------------------
# DISPLAY CHAT
# -------------------------------
for role, text in st.session_state.chat_history:
    st.chat_message(role).write(text)