import asyncio
from typing import Dict, AsyncGenerator, Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Request, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import joblib
import pandas as pd

from .config import settings
from .hand_detection import detect_hands
from .utils import mediapipe_landmarks_to_angles


app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global dictionary to hold image queues and latest predictions per client
image_queues: Dict[str, asyncio.Queue] = {}
latest_predictions: Dict[str, Optional[str]] = (
    {}
)  # Holds the latest prediction for each client

rf_model = joblib.load("app/rf_model.pkl")


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request) -> HTMLResponse:
    # Serve the main index page
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_image/{client_id}")
async def process_image(
    client_id: str, image: UploadFile = File(...)
) -> Dict[str, str]:
    # Read image data and update the client's image queue
    contents = await image.read()
    await update_client_queue(client_id, contents)
    return {"status": "success"}


@app.get("/latest_result/{client_id}")
async def get_latest_result(client_id: str) -> Dict[str, Optional[str]]:
    # Return the latest prediction for the given client_id
    if client_id in latest_predictions:
        return {
            "client_id": client_id,
            "latest_prediction": latest_predictions[client_id],
        }
    else:
        raise HTTPException(status_code=404, detail=f"Client ID {client_id} not found")


async def update_client_queue(client_id: str, image_data: bytes) -> None:
    # Initialize a new queue for the client if it does not exist
    if client_id not in image_queues:
        image_queues[client_id] = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        latest_predictions[client_id] = None  # Initialize latest prediction as None

    # Remove oldest image if the queue is full
    if image_queues[client_id].full():
        await image_queues[client_id].get()

    # Add new image data to the queue
    await image_queues[client_id].put(image_data)


async def get_next_frame(client_id: str) -> np.ndarray:
    try:
        # Retrieve the next image frame from the queue with a timeout
        img_data = await asyncio.wait_for(
            image_queues[client_id].get(),
            timeout=settings.FRAME_TIMEOUT,
        )
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image")
        return frame
    except asyncio.TimeoutError:
        # Raise a 408 error if fetching the frame times out
        raise HTTPException(status_code=408, detail="Frame fetch timeout")
    except Exception as e:
        # Raise a 500 error for general frame processing errors
        raise HTTPException(
            status_code=500,
            detail=f"Frame processing error: {str(e)}",
        )


async def generate_frames(client_id: str) -> AsyncGenerator[bytes, None]:
    try:
        # Ensure the client's queue is ready
        await wait_for_client_queue(client_id)
        # Continuously process and yield frames
        async for frame in process_frames(client_id):
            yield frame
    finally:
        # Cleanup resources when done
        cleanup_client_resources(client_id)


async def wait_for_client_queue(client_id: str) -> None:
    # Retry until the client's queue is available or timeout
    for _ in range(settings.MAX_RETRIES):
        if client_id in image_queues:
            return
        await asyncio.sleep(settings.RETRY_DELAY)
    # Raise a 404 error if client ID is not found
    raise HTTPException(
        status_code=404,
        detail=f"Client ID {client_id} not found",
    )


def encode_frame(frame: np.ndarray) -> bytes:
    # Encode the frame as a JPEG image
    _, buffer = cv2.imencode(".jpg", frame)
    return buffer.tobytes()


async def process_frames(client_id: str) -> AsyncGenerator[bytes, None]:
    while True:
        try:
            # Get the next frame and process it
            frame = await get_next_frame(client_id)
            frame, multi_hand_landmarks = detect_hands(frame)

            # Process the hand landmarks to get angles
            if multi_hand_landmarks is not None:
                angles = mediapipe_landmarks_to_angles(multi_hand_landmarks[0])
                angles_array = np.array(angles).reshape(1, -1)
                # Define the correct feature names based on your training data
                feature_names = [f"angle_{i}" for i in range(angles_array.shape[1])]

                # Convert angles to a DataFrame with the correct feature names
                angles_df = pd.DataFrame(angles_array, columns=feature_names)

                # Predict using the RandomForest model
                prediction = rf_model.predict(angles_df)
                latest_predictions[client_id] = prediction[0]

            # Encode the processed frame
            frame_bytes = encode_frame(frame)

            # Yield the processed frame
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        except HTTPException as e:
            if e.status_code == 408:  # Handle timeout by sending an empty frame
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n\r\n"
            else:
                raise


def cleanup_client_resources(client_id: str) -> None:
    # Remove the client's queue to free resources
    image_queues.pop(client_id, None)
    latest_predictions.pop(client_id, None)  # Also remove the latest prediction


@app.get("/video_feed/{client_id}")
async def video_feed(client_id: str) -> StreamingResponse:
    # Stream the video feed for the specified client ID
    return StreamingResponse(
        generate_frames(client_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


def start_server():
    # Start the FastAPI server using Uvicorn
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
    )


if __name__ == "__main__":
    start_server()
