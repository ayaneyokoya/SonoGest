import cv2
import mediapipe as mp
from PIL import Image
import math

def detect_hand_gesture(hand_landmarks_list):
    if len(hand_landmarks_list) == 2:  # Two hands detected
        hand1 = hand_landmarks_list[0]
        hand2 = hand_landmarks_list[1]
        
        # Check if both hands are making OK gesture
        if is_ok_gesture(hand1) and is_ok_gesture(hand2):
            # Calculate distance between OK points of both hands
            h1_center_x = (hand1.landmark[4].x + hand1.landmark[8].x) / 2
            h1_center_y = (hand1.landmark[4].y + hand1.landmark[8].y) / 2
            h2_center_x = (hand2.landmark[4].x + hand2.landmark[8].x) / 2
            h2_center_y = (hand2.landmark[4].y + hand2.landmark[8].y) / 2
            
            dx = h1_center_x - h2_center_x
            dy = h1_center_y - h2_center_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Adjust normalization to start from minimum when hands are close
            normalized_distance = min(max(distance, 0.0), 0.8) / 0.8
            return ("pitch", normalized_distance)
    
    # Single hand gestures remain the same
    elif len(hand_landmarks_list) == 1:
        return detect_single_hand_gesture(hand_landmarks_list[0])
    
    return "hand_out"

def is_ok_gesture(hand_landmarks):
    # Check for OK gesture (thumb and index finger close)
    dx = hand_landmarks.landmark[4].x - hand_landmarks.landmark[8].x
    dy = hand_landmarks.landmark[4].y - hand_landmarks.landmark[8].y
    thumb_index_distance = math.sqrt(dx * dx + dy * dy)
    return thumb_index_distance < 0.05

def detect_single_hand_gesture(hand_landmarks):
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
    middle_folded = hand_landmarks.landmark[12].y > hand_landmarks.landmark[10].y
    ring_folded = hand_landmarks.landmark[16].y > hand_landmarks.landmark[14].y
    pinky_folded = hand_landmarks.landmark[20].y > hand_landmarks.landmark[18].y
    thumb_folded = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    
    # Return specific gestures
    if index_extended and middle_folded and ring_folded and pinky_folded and thumb_folded:
        return "index_up"
    elif index_extended and middle_extended and ring_folded and pinky_folded and thumb_folded:
        return "peace"

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
        max_num_hands=2,
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

        # Draw hand landmarks
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,  # Draw on the original frame
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    draw_spec,
                    draw_spec2
                )

            gesture = detect_hand_gesture(results.multi_hand_landmarks)
            if isinstance(gesture, tuple) and gesture[0] == "pitch":
                shared_data["gesture"] = gesture[0]
                shared_data["pitch_value"] = gesture[1]
                
                # Draw line between OK gestures
                hand1 = results.multi_hand_landmarks[0]
                hand2 = results.multi_hand_landmarks[1]
                
                # Calculate center points of OK gestures
                h1_center_x = int((hand1.landmark[4].x + hand1.landmark[8].x) / 2 * frame.shape[1])
                h1_center_y = int((hand1.landmark[4].y + hand1.landmark[8].y) / 2 * frame.shape[0])
                h2_center_x = int((hand2.landmark[4].x + hand2.landmark[8].x) / 2 * frame.shape[1])
                h2_center_y = int((hand2.landmark[4].y + hand2.landmark[8].y) / 2 * frame.shape[0])
                
                # Draw connecting line between OK gestures
                cv2.line(frame, (h1_center_x, h1_center_y), 
                        (h2_center_x, h2_center_y), (0, 255, 0), 2)
                
                # Draw circles at OK gesture points
                cv2.circle(frame, (h1_center_x, h1_center_y), 5, (255, 0, 0), -1)
                cv2.circle(frame, (h2_center_x, h2_center_y), 5, (255, 0, 0), -1)
                
                # Display distance value
                cv2.putText(frame, f"Pitch: {gesture[1]:.2f}", (10, 70),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
            else:
                shared_data["gesture"] = gesture
        else:
            shared_data["gesture"] = "hand_out"

        # Draw current gesture text
        cv2.putText(frame, f"Gesture: {shared_data['gesture']}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Convert the annotated frame to a PIL image for UI display
        frame_annotated = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_annotated)
        shared_data["pil_frame"] = pil_image

        if shared_data.get("stop"):
            break

    cap.release()