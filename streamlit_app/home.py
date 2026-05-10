"""
Home page for Streamlit authentication (Google OAuth).
"""

import streamlit as st

st.set_page_config(page_title="Login")

# Hide sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔐 Welcome to LangGraph Assistant")

# -------------------------------
# READ USER FROM URL
# -------------------------------
query_params = st.query_params

email = query_params.get("email")
name = query_params.get("name")

# If redirected from Google login
if email:
    st.session_state["user"] = {
        "email": email,
        "name": name
    }

# -------------------------------
# CHECK LOGIN
# -------------------------------
if "user" in st.session_state:
    user = st.session_state["user"]
    st.success(f"Logged in as {user.get('email')}")
    st.switch_page("pages/Chat.py")

# -------------------------------
# LOGIN BUTTON
# -------------------------------
st.markdown(
    """
    <a href="http://localhost:8080/auth/google">
        <button style="padding:12px 24px; font-size:16px;">
            Continue with Google
        </button>
    </a>
    """,
    unsafe_allow_html=True
)