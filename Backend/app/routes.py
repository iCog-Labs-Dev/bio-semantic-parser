from fastapi import APIRouter, WebSocket, Query, WebSocketDisconnect
from app.controllers import process_gse_pipeline  # assumed to be a sync function
from app.controllers import convert_fol_string_to_metta
from fastapi import Body
import asyncio
import json

router = APIRouter()
connections = {}

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    connections[client_id] = websocket
    try:
        while True:
            await websocket.receive_text()  # keep connection open
    except WebSocketDisconnect:
        connections.pop(client_id, None)

@router.post("/process")
async def run_pipeline(client_id: str = Query(...), gse_id: str = Query(...)):
    if not gse_id:
        return {"result": "GSE ID is required"}

    loop = asyncio.get_running_loop()

    # async wrapper to send progress
    async def send_progress(message: str):
        if client_id in connections:
            await connections[client_id].send_text(message)

    # sync-safe wrapper
    def progress_wrapper(message: str):
        asyncio.run_coroutine_threadsafe(send_progress(message), loop)

    # run sync function in thread pool
    result = await asyncio.to_thread(process_gse_pipeline, gse_id, send_progress=progress_wrapper)

    if client_id in connections:
        await connections[client_id].send_text(json.dumps(result))

    return {"status": "ok"}

@router.post("/convert_fol_to_metta")
async def convert_fol_to_metta(predicates_raw_string: str = Body(..., media_type="text/plain")):
    return convert_fol_string_to_metta(predicates_raw_string)
