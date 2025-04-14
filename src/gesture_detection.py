import cv2
import mediapipe as mp
from PIL import Image
import math

def get_finger_states(hand_landmarks):
    """Get extended/folded state of all fingers"""
    return {
        'index': hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y,
        'middle': hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y,
        'ring': hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y,
        'pinky': hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y,
        'thumb': hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x
    }

def get_ok_center(hand_landmarks):
    """Calculate center point of OK gesture (thumb and index)"""
    x = (hand_landmarks.landmark[4].x + hand_landmarks.landmark[8].x) / 2
    y = (hand_landmarks.landmark[4].y + hand_landmarks.landmark[8].y) / 2
    return x, y

def get_thumb_index_distance(hand_landmarks):
    """Calculate distance between thumb tip and index finger tip"""
    dx = hand_landmarks.landmark[4].x - hand_landmarks.landmark[8].x
    dy = hand_landmarks.landmark[4].y - hand_landmarks.landmark[8].y
    return math.sqrt(dx * dx + dy * dy)

def detect_single_hand_gesture(hand_landmarks):
    finger_states = get_finger_states(hand_landmarks)
    
    # Check for OK gesture
    thumb_index_distance = get_thumb_index_distance(hand_landmarks)
    if thumb_index_distance < 0.05:
        if all([finger_states['middle'], finger_states['ring'], finger_states['pinky']]):
            wrist_y = hand_landmarks.landmark[0].y
            reverb_intensity = 1 + (1 - wrist_y) * 10.0
            return ("reverb", reverb_intensity)
    
    # Check for peace sign (index and middle up, others down)
    if (finger_states['index'] and finger_states['middle'] and 
        not any([finger_states['ring'], finger_states['pinky'], finger_states['thumb']])):
        return "peace_up"
    
    # Determine gesture based on all five fingers
    extended_count = sum(finger_states.values())
    if extended_count >= 4:
        return "open_hand"
    elif extended_count == 0:
        return "closed_fist"
    else:
        return "neutral"

def detect_hand_gesture(hand_landmarks_list):
    if len(hand_landmarks_list) == 2:
        hand1, hand2 = hand_landmarks_list[0], hand_landmarks_list[1]
        
        if is_ok_gesture(hand1) and is_ok_gesture(hand2):
            h1_x, h1_y = get_ok_center(hand1)
            h2_x, h2_y = get_ok_center(hand2)
            
            distance = math.sqrt((h1_x - h2_x)**2 + (h1_y - h2_y)**2)
            normalized_distance = min(max(distance, 0.0), 0.8) / 0.8
            return ("pitch", normalized_distance)
    
    elif len(hand_landmarks_list) == 1:
        return detect_single_hand_gesture(hand_landmarks_list[0])
    
    return "hand_out"

def is_ok_gesture(hand_landmarks):
    # Check for OK gesture (thumb and index finger close)
    dx = hand_landmarks.landmark[4].x - hand_landmarks.landmark[8].x
    dy = hand_landmarks.landmark[4].y - hand_landmarks.landmark[8].y
    thumb_index_distance = math.sqrt(dx * dx + dy * dy)
    return thumb_index_distance < 0.05

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