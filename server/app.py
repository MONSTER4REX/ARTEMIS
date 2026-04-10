from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from artemis_env.environment import SOCEnv
from artemis_env.models import (
    ResetRequest,
    ResetResult,
    StepRequest,
    StepResult,
    StateResult,
)
env = SOCEnv()
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Artemis SOC Environment Server started.")
    yield
    print("Artemis SOC Environment Server shutting down.")
app = FastAPI(
    title="Artemis SOC Triage Benchmark API",
    description="A simulator for evaluating AI agents in security alert triage scenarios.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    index_path = os.path.join("server", "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "status": "online",
        "benchmark": "Artemis v1.1.0",
        "message": "Dashboard UI not found. Use /status for machine-readable state."
    }

@app.get("/status")
async def status_check():
    return {
        "status": "online",
        "benchmark": "Artemis v1.1.0",
        "active_episodes": len(env.active_episodes)
    }

static_path = os.path.join("server", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")
@app.post("/reset", response_model=ResetResult)
async def reset_episode(request: ResetRequest = ResetRequest()):
    try:
        result = env.reset(task=request.task, seed=request.seed)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset episode: {str(e)}"
        )
@app.post("/step", response_model=StepResult)
async def step_episode(request: StepRequest):
    if not request.episode_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="episode_id is required."
        )
    try:
        result = env.step(episode_id=request.episode_id, action=request.action)
        if result.error and "not found" in result.error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.error
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing step: {str(e)}"
        )
@app.get("/state", response_model=StateResult)
async def get_state(episode_id: str):
    result = env.get_state(episode_id=episode_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode '{episode_id}' not found."
        )
    return result
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"An unhandled error occurred: {str(exc)}"}
    )

def main():
    """Entry point for the server as required by the OpenEnv validator."""
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()