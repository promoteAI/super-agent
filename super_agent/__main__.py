"""API main module."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.logging import DefaultFormatter

from super_agent.api.agent.initagent import initialise_agent_registry
from super_agent.api.agent.router import router as v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))


@asynccontextmanager
async def lifespan(
    app: FastAPI,  # pylint: disable=unused-argument, redefined-outer-name
):
    """Application lifespan context manager."""
    await initialise_agent_registry()
    yield


app = FastAPI(
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "agent",
            "description": "List and interact with agents.",
        }
    ],
)

# Define the origins that are allowed to make cross-origin requests
origins = [
    "http://localhost:8000",  # React app running on localhost:3000
    "http://127.0.0.1:8000",  # Alternative localhost
    # Add other origins if needed
]

# Add the CORSMiddleware to the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/", description="Get a greeting message.")
async def get() -> dict:
    """Return a greeting message.

    Returns:
        dict: A dictionary containing a greeting message.

    """
    return {"message": "Hello, World!"}


api = APIRouter(prefix="/api")
api.include_router(v1_router)
app.include_router(api)