import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

def start_ui(shared_data):
    root = tk.Tk()
    root.title("SonoGest - Audio Gesture Control")
    
    # Set a default window size
    root.geometry("800x600")

    # Create a frame that fills the entire window
    video_frame = tk.Frame(root)
    video_frame.pack(fill="both", expand=True)

    # Disable geometry propagation so the frame won't auto-resize the root
    video_frame.pack_propagate(False)

    # Place the video label inside the frame
    video_label = tk.Label(video_frame)
    video_label.pack(fill="both", expand=True)

    # Label for the gesture text
    gesture_label = ttk.Label(root, text="Current Gesture: None", font=("Arial", 16))
    gesture_label.pack()

    def update_ui():
        # Update gesture label
        current_gesture = shared_data.get("gesture", "None")
        gesture_label.config(text=f"Current Gesture: {current_gesture}")

        # Update the video feed if available
        pil_frame = shared_data.get("pil_frame")
        if pil_frame is not None:
            frame_width = video_label.winfo_width()
            frame_height = video_label.winfo_height()
            
            # If the frame hasn't been drawn yet, set default dims
            if frame_width < 2 or frame_height < 2:
                frame_width, frame_height = 640, 480

            # Resize while preserving aspect ratio (optional)
            image_aspect = pil_frame.width / pil_frame.height
            label_aspect = frame_width / frame_height

            if label_aspect > image_aspect:
                # Limited by height
                new_height = frame_height
                new_width = int(image_aspect * new_height)
            else:
                # Limited by width
                new_width = frame_width
                new_height = int(new_width / image_aspect)

            resized_frame = pil_frame.resize((new_width, new_height))
            photo = ImageTk.PhotoImage(resized_frame)
            video_label.config(image=photo)
            video_label.image = photo

        root.after(30, update_ui)

    def on_closing():
        shared_data["stop"] = True
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    update_ui()
    root.mainloop()