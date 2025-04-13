import pyaudio
import numpy as np
from pedalboard import Pedalboard, Reverb, Chorus, Delay

class AudioEffects:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        # Initialize effects chains with more intense reverb settings
        self.reverb_board = Pedalboard([
            Reverb(
                room_size=0.9,    # Increased from 0.8
                damping=0.2,      # Decreased from 0.5 for longer decay
                wet_level=0.9,    # Increased from 0.8
                dry_level=0.1,    # Decreased from 0.2
                width=1.0         # Added stereo width parameter
            )
        ])
        
        self.chorus_board = Pedalboard([
            Chorus(
                rate_hz=3.0,
                depth=0.5,
                centre_delay_ms=7.0,
                mix=0.5
            )
        ])
        
        self.delay_board = Pedalboard([
            Delay(
                delay_seconds=0.2,
                feedback=0.4,
                mix=0.5
            )
        ])

    def apply_reverb(self, audio, intensity=1.0):
        """Apply reverb effect with variable intensity"""
        # More dramatic intensity scaling
        self.reverb_board[0].room_size = min(1.0, 0.7 + intensity * 0.3)
        self.reverb_board[0].wet_level = min(1.0, intensity)
        self.reverb_board[0].damping = max(0.1, 0.5 - intensity * 0.4)
        return self.reverb_board(audio, self.sample_rate)

    def apply_chorus(self, audio):
        """Apply chorus effect"""
        return self.chorus_board(audio, self.sample_rate)

    def apply_delay(self, audio):
        """Apply delay effect"""
        return self.delay_board(audio, self.sample_rate)

def run_audio_processing(shared_data):
    p = pyaudio.PyAudio()
    frames_per_buffer = 2048
    sample_rate = 44100
    
    # Initialize audio effects
    effects = AudioEffects(sample_rate=sample_rate)
    
    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        output=True,
                        frames_per_buffer=frames_per_buffer)
    except Exception as e:
        print("Error opening audio stream:", e)
        return

    # State machine: "idle", "recording", "playing"
    state = "idle"
    recorded_frames = []  # List to hold NumPy arrays of recorded audio
    audio_loop = None     # Finalized loop as a NumPy array
    playback_pointer = 0  # Pointer for loop playback

    while True:
        if shared_data.get("stop"):
            break

        try:
            data = stream.read(frames_per_buffer, exception_on_overflow=False)
        except Exception as e:
            print("Audio stream error:", e)
            continue

        gesture = shared_data.get("gesture", "hand_out")

        if gesture == "open_hand":
            if state != "recording":
                print("Starting recording loop...")
                recorded_frames = []
                state = "recording"
            # Only store the recorded audio, don't play it back
            recorded_frames.append(np.frombuffer(data, dtype=np.float32))

        elif gesture == "closed_fist":
            if state == "recording":
                print("Recording ended. Starting playback loop...")
                state = "playing"
                if recorded_frames:
                    audio_loop = np.concatenate(recorded_frames)
                else:
                    audio_loop = np.array([], dtype=np.float32)
                playback_pointer = 0

            if state == "playing" and audio_loop is not None and audio_loop.size > 0:
                # Only output audio during loop playback
                end_pointer = playback_pointer + frames_per_buffer
                chunk = audio_loop[playback_pointer:end_pointer]
                if chunk.size < frames_per_buffer:
                    remainder = frames_per_buffer - chunk.size
                    chunk = np.concatenate((chunk, audio_loop[:remainder]))
                    playback_pointer = remainder
                else:
                    playback_pointer = end_pointer
                stream.write(chunk.astype(np.float32).tobytes())

        elif gesture == "reverb":
            if state == "playing" and audio_loop is not None and audio_loop.size > 0:
                end_pointer = playback_pointer + frames_per_buffer
                chunk = audio_loop[playback_pointer:end_pointer]
                if chunk.size < frames_per_buffer:
                    remainder = frames_per_buffer - chunk.size
                    chunk = np.concatenate((chunk, audio_loop[:remainder]))
                    playback_pointer = remainder
                else:
                    playback_pointer = end_pointer
                
                # Get hand height for effect intensity (0.0 to 1.0)
                intensity = shared_data.get("hand_height", 0.5)
                # Apply effect
                chunk = effects.apply_reverb(chunk, intensity)
                stream.write(chunk.astype(np.float32).tobytes())

        elif gesture == "hand_out":
            if state != "idle":
                print("Hand out detected. Stopping loop and reverting to live audio.")
                state = "idle"
                recorded_frames = []
                audio_loop = None

        else:
            # For "neutral" or any other state, only play if there's an active loop
            if state == "playing" and audio_loop is not None and audio_loop.size > 0:
                end_pointer = playback_pointer + frames_per_buffer
                chunk = audio_loop[playback_pointer:end_pointer]
                if chunk.size < frames_per_buffer:
                    remainder = frames_per_buffer - chunk.size
                    chunk = np.concatenate((chunk, audio_loop[:remainder]))
                    playback_pointer = remainder
                else:
                    playback_pointer = end_pointer
                stream.write(chunk.astype(np.float32).tobytes())

    stream.stop_stream()
    stream.close()
    p.terminate()