from fastapi import FastAPI
from app.routes import router as upload_router

app = FastAPI(
    title="Flatdrop API",
    description="Local REST API to push .md files into the Flatline Codex vault.",
    version="0.1.0"
)

app.include_router(upload_router)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

