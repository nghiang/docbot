"""
DocBot Backend — FastAPI application.
Handles file uploads, triggers indexing, search, and QA via Gemini.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from routers import auth_router, conversations_router, chat_router, documents_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="DocBot",
    description="Document QA Chatbot powered by Gemini",
    version="1.0.0",
)

# Prometheus metrics
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True, 
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(documents_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
