from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as upload_router

app = FastAPI(
    title="Flatdrop API",
    description="Local REST API to push .md files into the Flatline Codex vault.",
    version="0.1.0"
)

# CRITICAL: Add CORS middleware BEFORE including routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Now add the router
app.include_router(upload_router)
