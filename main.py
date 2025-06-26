
import shutil
import os
import time # For X-Process-Time middleware
from utils.logger import LOGGER
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware # For CORS
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from routes.chat_assistant import CHAT_ASSISTANT_ROUTER 

app = FastAPI(
    title="AI Coding Assistant API",
    description="Upload codebases and ask questions about them. Endpoints are now in a separate router.",
    version="0.2.0", # Incremented version    
)

# --- Middleware ---

# 1. CORS Middleware
# Define allowed origins for CORS (Cross-Origin Resource Sharing)
# Adjust this list based on where your frontend/clients will be running
origins = [
    "http://localhost",
    "http://localhost:3000", # Example for a React frontend
    "http://127.0.0.1",
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True, # Allows cookies to be included in cross-origin requests
    allow_methods=["*"],    # Allows all standard HTTP methods
    allow_headers=["*"],    # Allows all headers
)

# 2. Custom Middleware to add X-Process-Time header
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Adds a custom X-Process-Ti
    
    me header to responses, indicating how long
    the request took to process.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    LOGGER.info(f"Request {request.method} {request.url.path} processed in {process_time:.4f}s")
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handles any exception that is not caught by a more specific handler
    within this FastAPI application instance.
    Returns a JSON response with a 500 status code and an error message.
    """
    # It's good practice to log the actual exception for debugging purposes.
    # In a production environment, you'd likely use a more robust logging library.
    LOGGER.info(f"An unhandled exception occurred: {exc}")
    LOGGER.info(f"Request details: {request.method} {request.url.path}")
    # You could add more details from 'exc' or 'request' to your logs if needed.

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected internal server error occurred. Please try again later or contact support."
        },
    )

app.include_router(CHAT_ASSISTANT_ROUTER, prefix="/api/v1")