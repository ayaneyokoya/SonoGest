# SonoGest

SonoGest is a gesture-controlled audio production tool that enables hands-free control of Ableton Live through computer vision. Using real-time hand gesture detection, producers and musicians can control recording, playback, and audio effects without touching their computer.

## Features
- **Gesture Controls:**
  - Open Hand: Start recording
  - Closed Fist: Stop recording and playback
  - Peace Sign: Record in next scene
  - Dual OK Gestures: Control pitch shifting (-48 to +48 semitones)
  - OK Gesture Height: Control reverb intensity

- **Real-time Processing:**
  - Live webcam feed with gesture visualization
  - Immediate audio control response
  - Visual feedback of current gesture and effects

- **Ableton Live Integration:**
  - Session View recording control
  - Real-time pitch manipulation
  - Scene management
  - Track arming and monitoring

## Prerequisites
- Ableton Live 11 or higher
- Python 3.8+
- Webcam
- AbletonOSC plugin installed

## Setup Instructions
1. Install AbletonOSC:
   ```bash
   # Copy AbletonOSC to Ableton MIDI Remote Scripts folder
   cp -r AbletonOSC ~/Music/Ableton/User\ Library/Remote\ Scripts/
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure Ableton Live:
   - Open Preferences > Link/MIDI
   - Select "AbletonOSC" in Control Surface dropdown
   - Verify "Listening for OSC on port 11000" message

5. Run SonoGest:
   ```bash
   python run.py
   ```

## System Requirements
- macOS 10.15 or higher
- Ableton Live 11+
- Python 3.8+
- Webcam with minimum 720p resolution
- 8GB RAM recommended

## Project Structure
```
SonoGest/
├── src/
│   ├── gesture_detection.py  # Hand tracking and gesture recognition
│   ├── audio_processing.py   # Ableton Live OSC control
│   ├── ui.py                 # Tkinter interface
│   └── run.py               # Main application entry
├── requirements.txt
└── README.md
```

## Acknowledgments
- Built with MediaPipe for hand tracking
- Uses AbletonOSC for DAW control
- OpenCV for video processing
- Tkinter for user interface