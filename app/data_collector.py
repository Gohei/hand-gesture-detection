import cv2
import csv
import os
from datetime import datetime
from .hand_detection import detect_hands

# Create datasets directory if it doesn't exist
datasets_dir = "datasets"
raw_data_dir = os.path.join(datasets_dir, "raw_data")
os.makedirs(raw_data_dir, exist_ok=True)

# CSV file setup
csv_filename = os.path.join(
    raw_data_dir,
    f"hand_gesture_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
)
csv_header = ["timestamp", "gesture"] + [
    f"landmark_{i}_{axis}" for i in range(21) for axis in "xyz"
]

with open(csv_filename, "w", newline="") as file:
    csv.writer(file).writerow(csv_header)

# Gesture mapping and counters
gesture_map = {"r": "rock", "p": "paper", "s": "scissors"}
gesture_counts = {gesture: 0 for gesture in gesture_map.values()}
current_gesture = "none"
is_collecting = False

capture = cv2.VideoCapture(0)

while capture.isOpened():
    success, frame = capture.read()
    if not success:
        print("Failed to capture frame. Skipping.")
        continue

    # Detect hands in the frame
    hands_frame, multi_hand_landmarks = detect_hands(frame)

    # Display current gesture and collection status
    cv2.putText(
        hands_frame,
        f"Gesture: {current_gesture}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        hands_frame,
        f"Collecting: {'Yes' if is_collecting else 'No'}",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )

    # Display gesture counts
    y_offset = 110
    for gesture, count in gesture_counts.items():
        cv2.putText(
            hands_frame,
            f"{gesture}: {count}",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        y_offset += 40

    cv2.imshow("Janken Gesture Collector", hands_frame)

    # Handle key presses
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key in [ord(k) for k in gesture_map.keys()]:
        current_gesture = gesture_map[chr(key)]
    elif key == ord("c"):
        is_collecting = not is_collecting

    # Save data if collecting and hand is detected
    if is_collecting and multi_hand_landmarks:
        data = [datetime.now().isoformat(), current_gesture]
        for landmark in multi_hand_landmarks[0].landmark:
            data.extend([landmark.x, landmark.y, landmark.z])

        with open(csv_filename, "a", newline="") as file:
            csv.writer(file).writerow(data)

        # Increment the counter for the current gesture
        if current_gesture in gesture_counts:
            gesture_counts[current_gesture] += 1

capture.release()
cv2.destroyAllWindows()

# Print final counts
print("\nFinal gesture counts:")
for gesture, count in gesture_counts.items():
    print(f"{gesture}: {count}")
