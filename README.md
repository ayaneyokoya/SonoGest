# SonoGest

SonoGest is a computer visualization project that uses real-time hand gesture detection via a webcam to control and manipulate audio effects. It leverages MediaPipe for hand tracking, OpenCV for video processing, PyAudio for audio streaming, and Tkinter for a simple user interface.

## Features
- Real-time hand gesture detection
- Mapping of specific gestures to audio effects (e.g., volume control)
- Audio processing using live microphone input
- Simple UI display of the current gesture

## Setup Instructions
1. Create and activate a virtual environment:
    ```bash
    python -m venv env
    # Windows:
    .\env\Scripts\activate
    # macOS/Linux:
    source env/bin/activate
    ```
2. Install the required packages:
    ```bash
    pip install opencv-python mediapipe pyaudio numpy Pillow
    ```
3. Run the project:
    ```bash
    python run.py
    ```