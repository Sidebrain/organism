import os
from typing import AsyncGenerator

import socketio  # type: ignore[import-untyped]
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from core.api.v1.router import router as v1_router
from core.sockets import register_sio_handlers, sio

## SETTINGS
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
]


## FUNCTIONS
def check_env_vars() -> bool:
    load_dotenv(override=True, dotenv_path=".env.local")
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            return False
    return True


@asynccontextmanager
async def lifecycle_manager(self) -> AsyncGenerator[None, None]:
    print("Starting FastAPI app")
    print("Loading Env Variables")
    if not check_env_vars():
        raise ValueError("Missing required environment variables")

    # register socketio handlers
    register_sio_handlers()

    yield
    print("Shutting down FastAPI app")


fastapi_app = FastAPI(lifespan=lifecycle_manager)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


fastapi_app.include_router(v1_router)


@fastapi_app.get("/")
async def index() -> dict[str, str]:
    return {"message": "Hello World"}


app = socketio.ASGIApp(sio, fastapi_app)
