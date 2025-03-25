import cv2
import mediapipe as mp
from PIL import Image
import math

def detect_hand_gesture(hand_landmarks):
    # Compute distance between thumb tip (4) and index finger tip (8)
    dx = hand_landmarks.landmark[4].x - hand_landmarks.landmark[8].x
    dy = hand_landmarks.landmark[4].y - hand_landmarks.landmark[8].y
    thumb_index_distance = math.sqrt(dx * dx + dy * dy)
    
    # Check for "OK" hand signal (reverb gesture):
    # If thumb and index are close together (below threshold) and the other three fingers are extended.
    ok_threshold = 0.05  # Adjust threshold as needed
    if thumb_index_distance < ok_threshold:
        middle_extended = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
        ring_extended = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
        pinky_extended = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
        if middle_extended and ring_extended and pinky_extended:
            # Use the wrist's y-coordinate (landmark 0) to determine reverb intensity.
            # Normalized y goes from 0 at the top to 1 at the bottom.
            # When the hand is low (wrist_y near 1), reverb intensity is 1 (lowest).
            # When the hand is high (wrist_y near 0), reverb intensity increases.
            wrist_y = hand_landmarks.landmark[0].y
            scale_factor = 10.0  # Adjust this factor for how much reverb you want at maximum.
            reverb_intensity = 1 + (1 - wrist_y) * scale_factor
            # Return a tuple with the gesture "reverb" and the computed intensity.
            return ("reverb", reverb_intensity)
    
    # Otherwise, determine gesture based on all five fingers.
    index_extended = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    middle_extended = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    ring_extended = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
    pinky_extended = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
    thumb_extended = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x

    extended_count = sum([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended])
    if extended_count >= 4:
        return "open_hand"
    elif extended_count == 0:
        return "closed_fist"
    else:
        return "neutral"

def run_gesture_detection(shared_data):
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    draw_spec = mp_draw.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4)
    draw_spec2 = mp_draw.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)

    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip frame for mirror effect
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            shared_data["gesture"] = "hand_out"
        else:
            for handLms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS, draw_spec, draw_spec2)
                gesture = detect_hand_gesture(handLms)
                if isinstance(gesture, tuple):
                    shared_data["gesture"] = gesture[0]
                    shared_data["reverb_intensity"] = gesture[1]
                else:
                    shared_data["gesture"] = gesture
                break

        # Convert the annotated frame to a PIL image for UI display
        frame_annotated = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_annotated)
        shared_data["pil_frame"] = pil_image

        if shared_data.get("stop"):
            break

    cap.release()