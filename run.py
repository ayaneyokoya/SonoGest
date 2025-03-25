import threading
from src import gesture_detection, audio_processing, ui

def main():
    # Shared data dictionary to communicate the current gesture across modules
    shared_data = {"gesture": "neutral"}
    
    # Create threads for gesture detection and audio processing only
    gesture_thread = threading.Thread(target=gesture_detection.run_gesture_detection, args=(shared_data,))
    audio_thread = threading.Thread(target=audio_processing.run_audio_processing, args=(shared_data,))

    # Start the non-UI threads
    gesture_thread.start()
    audio_thread.start()

    # Run the UI on the main thread
    ui.start_ui(shared_data)

    # Wait for the non-UI threads to finish
    gesture_thread.join()
    audio_thread.join()

if __name__ == "__main__":
    main()
    
    