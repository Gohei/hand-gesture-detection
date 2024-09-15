import numpy as np
import pandas as pd
from typing import List, Tuple

# 定数として各指の関節番号を定義
FINGER_INDICES = {
    "thumb": [0, 1, 2, 3, 4],
    "index_finger": [0, 5, 6, 7, 8],
    "middle_finger": [0, 9, 10, 11, 12],
    "ring_finger": [0, 13, 14, 15, 16],
    "pinky": [0, 17, 18, 19, 20],
}
import numpy as np
from typing import List


def mediapipe_landmarks_to_angles(hand_landmarks) -> List[float]:
    # MediaPipeのランドマークをnumpy配列に変換
    landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])

    angles = []
    for finger in FINGER_INDICES.values():
        for i in range(len(finger) - 2):
            p1 = landmarks[finger[i]]
            p2 = landmarks[finger[i + 1]]
            p3 = landmarks[finger[i + 2]]
            angle = calculate_angle(p1, p2, p3)
            angles.append(angle)

    return angles


def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    v1 = p1 - p2
    v2 = p3 - p2
    cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)


def calculate_hand_angles(landmarks: List[List[float]]) -> List[float]:
    angles = []
    for finger in FINGER_INDICES.values():
        for i in range(len(finger) - 2):
            p1 = np.array(landmarks[finger[i]])
            p2 = np.array(landmarks[finger[i + 1]])
            p3 = np.array(landmarks[finger[i + 2]])
            angle = calculate_angle(p1, p2, p3)
            angles.append(angle)
    return angles


def process_and_save_angles(input_file: str, output_file: str):
    df = pd.read_csv(input_file)

    all_angles = []
    for _, row in df.iterrows():
        landmarks = [[row[f"landmark_{i}_{axis}"] for axis in "xyz"] for i in range(21)]
        angles = calculate_hand_angles(landmarks)
        all_angles.append(angles)

    angles_df = pd.DataFrame(all_angles)
    angles_df["timestamp"] = df["timestamp"]
    angles_df["gesture"] = df["gesture"]

    angles_df.to_csv(output_file, index=False)
    print(f"Angles saved to {output_file}")


def load_angles_from_csv(
    file_path: str,
) -> Tuple[List[List[float]], List[str], List[str]]:
    df = pd.read_csv(file_path)
    angles = df.iloc[:, :-2].values.tolist()
    timestamps = df["timestamp"].tolist()
    gestures = df["gesture"].tolist()
    return angles, timestamps, gestures
