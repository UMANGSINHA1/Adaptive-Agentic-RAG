"""
Main FastAPI application entry point with Google OAuth.
"""

import os
from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

from src.api.routes import router

app = FastAPI(title="Adaptive RAG API")

# -------------------------------
# Session Middleware
# -------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key="your_secret_key_here",
    same_site="lax",
    https_only=False
)

# -------------------------------
# OAuth Setup
# -------------------------------
oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# -------------------------------
# Routes
# -------------------------------
app.include_router(router)
app.state.description_ = ""


@app.get("/")
async def root():
    return {"message": "Adaptive RAG API is running"}


# -------------------------------
# Google Login
# -------------------------------
@app.get("/auth/google")
async def login_via_google(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


# -------------------------------
# Google Callback
# -------------------------------
@app.get("/auth/google/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)

    user = token.get("userinfo")

    if not user:
        user = await oauth.google.parse_id_token(request, token)

    # Extract info
    email = user.get("email", "")
    name = user.get("name", "")

    # 🔥 IMPORTANT: redirect with user data
    return RedirectResponse(
        url=f"http://localhost:8501/?email={email}&name={name}"
    )


# -------------------------------
# Get Logged-in User
# -------------------------------
@app.get("/auth/me")
async def get_user(request: Request):
    return request.session.get("user", {})


# -------------------------------
# Logout
# -------------------------------
@app.get("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}