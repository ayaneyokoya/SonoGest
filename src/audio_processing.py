import subprocess
from pythonosc import udp_client

class AbletonController:
    def __init__(self):
        # AbletonOSC listens on port 11000 and sends replies on 11001
        self.client = udp_client.SimpleUDPClient("127.0.0.1", 11000)
        print("Initialized AbletonOSC client on port 11000")
        
    def send_osc(self, address, value):
        try:
            self.client.send_message(address, value)
            print(f"DEBUG - Sent OSC message:")
            print(f"  Address: {address}")
            print(f"  Value: {value}")
        except Exception as e:
            print(f"ERROR - Failed to send OSC message:")
            print(f"  Address: {address}")
            print(f"  Value: {value}")
            print(f"  Error: {str(e)}")

    def set_pitch(self, value):
        """
        Set pitch for clip 1 in track 0 using normalized distance value between OK gestures.
        Args:
            value: Float 0-1 representing normalized distance between OK gestures
        """
        # Map 0-1 to -48 to +48 range for pitch shifting
        pitch_value = int((value * 96) - 48)
            
        # Set pitch for clip
        self.send_osc("/live/clip/set/pitch_coarse", [0, 0, pitch_value])
        
        # Debug output
        print(f"Setting clip pitch to {pitch_value} semitones")
        
        # Verify pitch was set
        self.send_osc("/live/clip/get/pitch_coarse", [0, 0])

    def start_recording(self):
        # Starts playing scene
        self.send_osc("/live/scene/fire", 0)
        # Arm track 0
        self.send_osc("/live/track/set/arm", [0, 1])
        # Start recording
        self.send_osc("/live/song/set/session_record", 1)

    def stop_recording(self):
        """Stop recording and play back the recorded section"""
        # Stop recording mode
        self.send_osc("/live/song/set/session_record", 0)
        
        # Get current song position as the end point
        self.send_osc("/live/song/get/current_song_time", None)
        
        # Return to start of recorded section
        self.send_osc("/live/song/set/current_song_time", 0)
        
        # Disarm track
        self.send_osc("/live/track/set/arm", [0, 0])
        
        # # Undo solo if active
        # self.send_osc("/live/track/set/solo", [0, 0])
        
        # Start playback
        self.send_osc("/live/song/continue_playing", 1)
        
    # Peace up = Record next scene
    def next_scene(self):
        # Begins playing scene 1
        self.send_osc("/live/scene/fire", 1)
        # Start recording
        self.send_osc("/live/song/set/session_record", 1)
         # Arm track 0
        self.send_osc("/live/track/set/arm", [0, 1])
        
    def neutral(self):
        # self.send_osc("/live/track/set/solo", [0, 0])
        self.send_osc("/live/track/set/arm", [0, 0])
        

def run_audio_processing(shared_data):
    controller = AbletonController()
    state = "idle"

    while True:
        if shared_data.get("stop"):
            break

        gesture = shared_data.get("gesture", "hand_out")

        if gesture == "open_hand":
            if state != "recording":
                print("Starting Ableton recording...")
                state = "recording"
                controller.start_recording()

        elif gesture == "closed_fist":
            if state == "recording":
                print("Stopping recording and starting loop playback...")
                state = "idle"
                controller.stop_recording()

        elif gesture == "hand_out":
            if state != "idle":
                print("Hand out detected. Going back to neutral state.")
                state = "idle"
                controller.neutral()
                
        elif gesture == "pitch":
            pitch_value = shared_data.get("pitch_value", 0.5)
            print(f"Adjusting pitch... Value: {pitch_value}")
            controller.set_pitch(pitch_value)
            
        elif gesture == "peace_up":
            print("Recording next scene...")
            state = "recording"
            controller.next_scene()
        else: 
            controller.neutral()
            state = "idle"