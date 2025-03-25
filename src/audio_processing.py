import pyaudio
import numpy as np

def apply_reverb_effect(signal, tail_duration=2.0, sample_rate=22050):
    """
    Applies an extreme hall echo reverb to the entire signal using convolution
    with a long impulse response, then normalizes the output so that its peak
    amplitude matches the original signal.
    
    Parameters:
      signal: NumPy array of the complete audio loop.
      tail_duration: Duration in seconds of the reverb tail (e.g., 2.0 seconds).
      sample_rate: The sample rate of the audio (default 44100).
    
    Returns:
      A NumPy array of the processed audio (clipped between -1 and 1) with the
      same peak volume as the input signal.
    """
    # Create an impulse response with a long tail.
    ir_length = int(sample_rate * tail_duration)
    t = np.linspace(0, tail_duration, ir_length)
    decay_rate = 0.3  # Slow decay for a long echo tail.
    ir = np.exp(-t * decay_rate)
    ir = ir / np.sum(ir)
    
    # Convolve the entire signal with the impulse response.
    conv = np.convolve(signal, ir, mode='full')[:signal.size]
    
    # Use a high wet mix for an extreme hall echo effect.
    mix = 0.9
    processed = (1 - mix) * signal + mix * conv
    
    # Normalize the processed signal to match the peak of the original signal.
    dry_peak = np.max(np.abs(signal))
    processed_peak = np.max(np.abs(processed))
    factor = dry_peak / processed_peak if processed_peak > 0 else 1.0
    out = processed * factor
    
    return np.clip(out, -1.0, 1.0)

def run_audio_processing(shared_data):
    p = pyaudio.PyAudio()
    frames_per_buffer = 2048
    try:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=44100,
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
            # Convert bytes to a NumPy array and store it
            recorded_frames.append(np.frombuffer(data, dtype=np.float32))
            # Optionally output live audio during recording
            stream.write(data)

        elif gesture == "closed_fist":
            if state == "recording":
                print("Recording ended. Starting playback loop...")
                state = "playing"
                # Finalize recording: concatenate the recorded frames into one array
                if recorded_frames:
                    audio_loop = np.concatenate(recorded_frames)
                else:
                    audio_loop = np.array([], dtype=np.float32)
                playback_pointer = 0

            if state == "playing" and audio_loop is not None and audio_loop.size > 0:
                # Create a playback chunk from the recorded audio
                end_pointer = playback_pointer + frames_per_buffer
                chunk = audio_loop[playback_pointer:end_pointer]
                if chunk.size < frames_per_buffer:
                    remainder = frames_per_buffer - chunk.size
                    # Loop back to the start for continuous playback
                    chunk = np.concatenate((chunk, audio_loop[:remainder]))
                    playback_pointer = remainder
                else:
                    playback_pointer = end_pointer
                stream.write(chunk.astype(np.float32).tobytes())
            else:
                stream.write(data)

        elif gesture == "reverb":
            # "OK" hand signal for reverb effect during playback
            if state == "playing" and audio_loop is not None and audio_loop.size > 0:
                end_pointer = playback_pointer + frames_per_buffer
                chunk = audio_loop[playback_pointer:end_pointer]
                if chunk.size < frames_per_buffer:
                    remainder = frames_per_buffer - chunk.size
                    chunk = np.concatenate((chunk, audio_loop[:remainder]))
                    playback_pointer = remainder
                else:
                    playback_pointer = end_pointer
                # Apply reverb effect to the playback chunk
                chunk = apply_reverb_effect(chunk)
                stream.write(chunk.astype(np.float32).tobytes())
            else:
                stream.write(data)

        elif gesture == "hand_out":
            if state != "idle":
                print("Hand out detected. Stopping loop and reverting to live audio.")
                state = "idle"
                recorded_frames = []
                audio_loop = None
            stream.write(data)

        else:
            # For "neutral" or any other state, continue playing loop if available
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
            else:
                stream.write(data)

    stream.stop_stream()
    stream.close()
    p.terminate()