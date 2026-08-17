import os
import subprocess
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.agent import run_agent

app = FastAPI(title="Autonomous Spreadsheet Agent")

# Mount output folder for downloads
os.makedirs("output", exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/static", StaticFiles(directory="frontend"), name="frontend")


@app.get("/")
async def serve_index():
    return FileResponse("frontend/index.html")


class OpenFileRequest(BaseModel):
    path: str


@app.post("/api/open-local")
async def open_local_file(req: OpenFileRequest):
    """Opens a generated file locally using the default system app (Excel)."""
    if os.path.exists(req.path):
        os.startfile(req.path)
        return {"status": "opened", "path": req.path}
    return {"status": "error", "message": "File not found"}


@app.websocket("/ws/agent")
async def agent_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def emit_to_client(event: dict):
        await websocket.send_json(event)

    try:
        while True:
            data = await websocket.receive_json()
            user_prompt = data.get("prompt", "")
            if not user_prompt:
                continue

            # Run autonomous agent loop and broadcast progress
            await run_agent(user_prompt, emit_to_client)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await emit_to_client({"type": "error", "message": str(e)})