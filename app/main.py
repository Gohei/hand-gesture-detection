from fastapi import FastAPI, File, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import cv2
import numpy as np
import joblib
import pandas as pd

from .config import settings
from .hand_detection import detect_hands
from .utils import mediapipe_landmarks_to_angles

app = FastAPI()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

rf_model = joblib.load("app/rf_model.pkl")


@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process_image")
async def process_image(
    image: UploadFile = File(...),
) -> dict[str, str | list[dict[str, float]] | None]:
    # Read image data
    img_data = await image.read()
    nparr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Detect hands and get landmarks
    frame, multi_hand_landmarks = detect_hands(frame)

    if multi_hand_landmarks is None:
        return {"gesture": "No hand detected", "landmarks": None}

    # Process the hand landmarks to get angles
    angles = mediapipe_landmarks_to_angles(multi_hand_landmarks[0])
    angles_array = np.array(angles).reshape(1, -1)

    # Define the correct feature names based on your training data
    feature_names = [f"angle_{i}" for i in range(angles_array.shape[1])]

    # Convert angles to a DataFrame with the correct feature names
    angles_df = pd.DataFrame(angles_array, columns=feature_names)

    # Predict using the RandomForest model
    prediction = rf_model.predict(angles_df)[0]

    # Get landmark coordinates
    landmarks: list[dict[str, float]] = [
        {"x": landmark.x, "y": landmark.y, "z": landmark.z}
        for landmark in multi_hand_landmarks[0].landmark
    ]

    return {"gesture": prediction, "landmarks": landmarks}


def start_server():
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL,
    )


if __name__ == "__main__":
    start_server()
