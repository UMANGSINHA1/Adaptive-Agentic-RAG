"""
API client for communicating with backend services (aligned with FastAPI backend).
"""

import requests

BASE_URL = "http://127.0.0.1:8080"


def get_api_token() -> str:
    """
    Get API token from backend.
    """
    response = requests.post(f"{BASE_URL}/init")

    if response.status_code == 200:
        return response.json().get("api_token", "")

    return ""


def create_user(username: str, password: str, api_token: str) -> bool:
    """
    Create user (dummy backend).
    """
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/create_user",
        json={"username": username, "password": password},
        headers=headers,
    )

    return response.status_code == 200


def login_user(username: str, password: str, api_token: str) -> dict:
    """
    Login user and get JWT token.
    """
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{BASE_URL}/login",
        json={"username": username, "password": password},
        headers=headers,
    )

    if response.status_code == 200:
        data = response.json()

        # Ensure both keys exist (important for frontend compatibility)
        return {
            "token": data.get("token", data.get("access_token", "")),
            "access_token": data.get("access_token", data.get("token", "")),
            "token_type": data.get("token_type", "bearer")
        }

    return {}


def query_backend(query: str, session_id: str) -> str:
    """
    Send query to RAG backend.
    """
    url = f"{BASE_URL}/rag/query"

    response = requests.post(
        url,
        json={
            "query": query,
            "session_id": session_id
        }
    )

    if response.status_code == 200:
        try:
            return response.json()["result"]["content"]
        except Exception:
            return str(response.json())

    return f"Error: {response.status_code} - {response.text}"


def document_upload_rag(file, description: str) -> bool:
    """
    Upload document to RAG backend.
    """
    url = f"{BASE_URL}/rag/documents/upload"

    if file:
        files = {
            "file": (file.name, file, file.type)
        }

        headers = {
            "X-Description": description
        }

        response = requests.post(url, files=files, headers=headers)

        return response.status_code == 200

    return False