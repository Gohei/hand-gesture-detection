import cv2
import numpy as np
import mediapipe as mp

# Setup Mediapipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize the Hands detector
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
)


def detect_hands(frame: np.ndarray):
    # Convert the frame to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Process the frame to detect hands
    results = hands.process(frame_rgb)

    # Create a black background
    black_frame = np.zeros_like(frame)
    multi_hand_landmarks = None

    # Check if hand landmarks were detected
    if results.multi_hand_landmarks:
        multi_hand_landmarks = results.multi_hand_landmarks
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw the hand landmarks on the black background
            mp_drawing.draw_landmarks(
                black_frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2),
            )

    # Return the frame with only the hands drawn on a black background
    return black_frame, multi_hand_landmarks
