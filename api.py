# src/api.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from src import gesture_detection, audio_processing
import threading

# Additional imports for video streaming
import cv2
import base64
import asyncio

app = FastAPI()

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust to match your front end's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global shared data for inter-thread communication.
shared_data = {"gesture": "neutral"}

# --- WebSocket Connection Manager for general use ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print("Received via WebSocket:", data)
            # Optionally process data (e.g., update shared_data) before broadcasting.
            await manager.broadcast({"message": "Received", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket client disconnected")

# --- Video Streaming WebSocket Endpoint ---
# --- Video Streaming WebSocket Endpoint using gesture detection frames ---
@app.websocket("/ws/video")
async def video_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        # Continuously check for a new frame from shared_data.
        while True:
            # Check if gesture detection has generated a new frame.
            pil_frame = shared_data.get("pil_frame")
            if pil_frame is not None:
                # Convert the PIL image to JPEG bytes.
                import io
                buf = io.BytesIO()
                pil_frame.save(buf, format="JPEG")
                frame_bytes = buf.getvalue()
                # Convert to base64 string.
                frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
                # Send the image over the WebSocket.
                await websocket.send_json({"image": frame_base64})
            await asyncio.sleep(0.033)  # Approximately 30 fps.
    except WebSocketDisconnect:
        print("Video WebSocket client disconnected")


# --- Data Streaming WebSocket Endpoint ---
@app.websocket("/ws/data")
async def data_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Create a safe dictionary from shared_data:
            safe_status = {
                "gesture": shared_data.get("gesture", "unknown"),
                "pitch_value": shared_data.get("pitch_value", 0)
            }
            # Send the updated status over the WebSocket.
            await websocket.send_json(safe_status)
            # Control update frequency (e.g., 10 times per second)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print("Data WebSocket client disconnected")


# --- Background Tasks ---
def run_background_tasks():
    # Start gesture detection and audio processing threads.
    gesture_thread = threading.Thread(target=gesture_detection.run_gesture_detection, args=(shared_data,))
    audio_thread = threading.Thread(target=audio_processing.run_audio_processing, args=(shared_data,))
    gesture_thread.start()
    audio_thread.start()
    app.state.gesture_thread = gesture_thread
    app.state.audio_thread = audio_thread

@app.on_event("startup")
async def startup_event():
    print("Starting background tasks...")
    run_background_tasks()
    print("Background tasks started.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down background tasks...")
    shared_data["stop"] = True  # Signal threads to stop
    app.state.gesture_thread.join()
    app.state.audio_thread.join()
    print("Background tasks terminated.")
