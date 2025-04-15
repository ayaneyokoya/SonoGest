// src/SubmarineMusicBoard.js
import React, { useState, useEffect, useRef } from 'react';
import { Mic, Video, Play, Pause, RefreshCw, Square, Hand, Music } from 'lucide-react';
import * as Tone from 'tone';
import './Sono.css'; // Import the CSS file
import useWebSocket from "./useWebSocket";
import useDataWebSocket from "./useDataWebSocket"; // Make sure this file exists and exports the data hook

// Helper: clamp a value to [min, max]
function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

// Helper: move a value toward a target by a step.
function moveToward(current, target, step) {
  if (Math.abs(current - target) < step) return target;
  return current > target ? current - step : current + step;
}

// Helper: update knob values based on gesture and intensity.
// (This is a declaration so it’s hoisted and available wherever needed.)
function updateKnobBasedOnGesture(gesture, intensity, synthRef, setKnobValues) {
  switch (gesture) {
    case "reverb":
      setKnobValues(prev => ({
        ...prev,
        reverb: clamp(intensity * 2, 0, 1),
        delay: clamp(intensity * 1.5, 0, 1)
      }));
      break;
    case "pitch":
      setKnobValues(prev => ({
        ...prev,
        freq: clamp(intensity, 0, 1),
        resonance: clamp(1 - intensity, 0, 1)
      }));
      if (synthRef.current) {
        const newFreq = 200 + (intensity * 500);
        synthRef.current.frequency.value = newFreq;
      }
      break;
    case "peace_up":
      setKnobValues(prev => ({
        ...prev,
        modulation: clamp(intensity * 1.2, 0, 1),
        delay: clamp(intensity, 0, 1)
      }));
      break;
    case "open_hand":
      setKnobValues({
        freq: 0.8,
        resonance: 0.7,
        delay: 0.6,
        reverb: 0.8,
        modulation: 0.7
      });
      break;
    case "closed_fist":
      setKnobValues({
        freq: 0.2,
        resonance: 0.3,
        delay: 0.1,
        reverb: 0.2,
        modulation: 0.1
      });
      break;
    case "neutral":
      setKnobValues(prev => ({
        freq: moveToward(prev.freq, 0.5, 0.1),
        resonance: moveToward(prev.resonance, 0.3, 0.1),
        delay: moveToward(prev.delay, 0.2, 0.1),
        reverb: moveToward(prev.reverb, 0.6, 0.1),
        modulation: moveToward(prev.modulation, 0.4, 0.1)
      }));
      break;
    default:
      break;
  }
}

const Sono = () => {
  // Component state
  const [isPlaying, setIsPlaying] = useState(false);
  const [webcamActive, setWebcamActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [knobValues, setKnobValues] = useState({
    freq: 90,
    resonance: 90,
    delay: 90,
    reverb: 90,
    modulation: 90,
  });
  const [gestureMode, setGestureMode] = useState(false);
  const [currentGesture, setCurrentGesture] = useState('hand_out');
  const [pitchValue, setPitchValue] = useState(0);

  // State for backend video stream frame (base64-encoded image)
  const [backendVideo, setBackendVideo] = useState("");

  // Get backend status using a dedicated data WebSocket hook.
  // This hook connects to your /ws/data endpoint and returns { gesture, pitch_value }.
  const dataFromWS = useDataWebSocket();

  // Refs for video, canvas, animations, and Tone objects
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const synthRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);

  // --- Map backend status to knob values and local state ---
  useEffect(() => {
    if (dataFromWS) {
      // Update knob values based on received gesture and pitch_value.
      if (dataFromWS.gesture === "reverb") {
        setKnobValues(prev => ({
          ...prev,
          reverb: clamp(dataFromWS.pitch_value, 90, 1),
          //delay: clamp(dataFromWS.pitch_value * 0.8, 0, 1)
        }));
      } else if (dataFromWS.gesture === "pitch") {
        setKnobValues(prev => ({
          ...prev,
          freq: clamp(1 - dataFromWS.pitch_value, 0, 1),
          //resonance: clamp(dataFromWS.pitch_value, 0, 1)
        }));
      }
      // Update local gesture and pitch state.
      setCurrentGesture(dataFromWS.gesture);
      setPitchValue(dataFromWS.pitch_value);
    }
  }, [dataFromWS]);

  // --- WebSocket integration for video streaming from the backend ---
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/video");
    ws.onopen = () => {
      console.log("Video WebSocket connected");
    };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.image) {
        setBackendVideo("data:image/jpeg;base64," + data.image);
      }
    };
    ws.onerror = (error) => {
      console.error("Video WebSocket error:", error);
    };
    ws.onclose = () => {
      console.log("Video WebSocket disconnected");
      setBackendVideo("");
    };
    return () => {
      ws.close();
    };
  }, []);

  // --- General WebSocket integration for gesture updates (optional) ---
  const { sendMessage } = useWebSocket((data) => {
    console.log("Backend update via WebSocket:", data);
  });
  useEffect(() => {
    sendMessage({ gesture: currentGesture, pitchValue });
  }, [currentGesture, pitchValue, sendMessage]);

  // --- Tone.js initialization and audio analyzer setup ---
  useEffect(() => {
    synthRef.current = new Tone.Synth().toDestination();
    const filter = new Tone.Filter(800, "lowpass").connect(Tone.Destination);
    const delay = new Tone.FeedbackDelay(0.3, 0.4).connect(filter);
    const reverb = new Tone.Reverb(3).connect(delay);
    synthRef.current.connect(reverb);

    analyserRef.current = Tone.context.createAnalyser();
    Tone.Destination.connect(analyserRef.current);
    analyserRef.current.fftSize = 64;
    const bufferLength = analyserRef.current.frequencyBinCount;
    dataArrayRef.current = new Uint8Array(bufferLength);

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (synthRef.current) synthRef.current.dispose();
    };
  }, []);

  // --- Local webcam setup functions for fallback ---
  const startWebcamFallback = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setWebcamActive(true);
        startMotionDetection();
      }
    } catch (err) {
      console.error("Error accessing webcam:", err);
    }
  };

  const stopWebcamFallback = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
      setWebcamActive(false);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    }
  };

  // --- Motion detection & gesture simulation (updates shared_data["pil_frame"]) ---
  const startMotionDetection = () => {
    if (!canvasRef.current || !videoRef.current) return;
    const ctx = canvasRef.current.getContext('2d');
    let previousImageData = null;
    const detectMotion = () => {
      if (!videoRef.current || !videoRef.current.videoWidth) {
        animationRef.current = requestAnimationFrame(detectMotion);
        return;
      }
      ctx.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
      const currentImageData = ctx.getImageData(0, 0, canvasRef.current.width, canvasRef.current.height);
      if (previousImageData) {
        const diff = calculateDifference(previousImageData.data, currentImageData.data);
        setAudioLevel(diff);
        if (gestureMode) {
          simulateHandGestureDetection(diff);
        } else {
          updateKnobsFromMotion(diff);
        }
      }
      previousImageData = currentImageData;
      animationRef.current = requestAnimationFrame(detectMotion);
    };
    animationRef.current = requestAnimationFrame(detectMotion);
  };

  const simulateHandGestureDetection = (motionLevel) => {
    const randomValue = Math.random();
    if (motionLevel > 40) {
      if (randomValue < 0.2) {
        setCurrentGesture("reverb");
        updateKnobBasedOnGesture("reverb", motionLevel / 100, synthRef, setKnobValues);
      } else if (randomValue < 0.4) {
        setCurrentGesture("pitch");
        const newPitch = Math.min(motionLevel / 100, 1);
        setPitchValue(newPitch);
        updateKnobBasedOnGesture("pitch", newPitch, synthRef, setKnobValues);
      } else if (randomValue < 0.6) {
        setCurrentGesture("peace_up");
        updateKnobBasedOnGesture("peace_up", motionLevel / 100, synthRef, setKnobValues);
      } else if (randomValue < 0.8) {
        setCurrentGesture("open_hand");
        updateKnobBasedOnGesture("open_hand", motionLevel / 100, synthRef, setKnobValues);
      } else {
        setCurrentGesture("closed_fist");
        updateKnobBasedOnGesture("closed_fist", motionLevel / 100, synthRef, setKnobValues);
      }
    } else if (motionLevel > 15) {
      if (randomValue < 0.3) {
        setCurrentGesture("neutral");
        updateKnobBasedOnGesture("neutral", motionLevel / 100, synthRef, setKnobValues);
      } else {
        setCurrentGesture("hand_out");
      }
    } else {
      setCurrentGesture("hand_out");
    }
  };

  const updateKnobsFromMotion = (motionLevel) => {
    setKnobValues(prev => {
      const randomFactor = Math.random() * 0.1;
      return {
        freq: clamp(prev.freq + (motionLevel > 50 ? 0.1 : -0.05) * randomFactor, 0, 1),
        resonance: clamp(prev.resonance + (motionLevel > 30 ? 0.08 : -0.04) * randomFactor, 0, 1),
        delay: clamp(prev.delay + (motionLevel > 20 ? 0.06 : -0.03) * randomFactor, 0, 1),
        reverb: clamp(prev.reverb + (motionLevel > 40 ? 0.07 : -0.035) * randomFactor, 0, 1),
        modulation: clamp(prev.modulation + (motionLevel > 15 ? 0.05 : -0.025) * randomFactor, 0, 1),
      };
    });
  };

  const calculateDifference = (prev, curr) => {
    let diff = 0;
    const sampleSize = Math.floor(prev.length / 100);
    for (let i = 0; i < prev.length; i += sampleSize * 4) {
      diff += Math.abs(prev[i] - curr[i]);
      diff += Math.abs(prev[i + 1] - curr[i + 1]);
      diff += Math.abs(prev[i + 2] - curr[i + 2]);
    }
    return Math.min(100, diff / 1000);
  };

  const toggleSound = async () => {
    if (!isPlaying) {
      await Tone.start();
      const now = Tone.now();
      synthRef.current.triggerAttack("C3", now);
      visualize();
    } else {
      synthRef.current.triggerRelease();
    }
    setIsPlaying(!isPlaying);
  };

  const visualize = () => {
    if (!analyserRef.current || !dataArrayRef.current) return;
    const updateVisualization = () => {
      if (!isPlaying) return;
      analyserRef.current.getByteFrequencyData(dataArrayRef.current);
      animationRef.current = requestAnimationFrame(updateVisualization);
    };
    animationRef.current = requestAnimationFrame(updateVisualization);
  };

  // Inline Knob component for simplicity.
  const Knob = ({ name, value, color }) => (
    <div className="flex flex-col items-center mx-2">
      <div className="knob" style={{ borderColor: color, transform: `rotate(${value * 270}deg)` }}>
        <div className="knob-pointer"></div>
      </div>
      <span className="knob-label">{name}</span>
    </div>
  );

  return (
    <div className="board-container">
      {/* (Optional) API status display */}
      <div className="api-status">
        {/* <p>API Status: Gesture - {apiStatus.gesture}</p>
        <p>API Status: Pitch - {apiStatus.pitch_value}</p> */}
      </div>



      <div className="submarine-container">
        <div className="submarine">
          <div className="red-light" />
          {/* Submarine windows */}
          <div className="windows">
            <div className="window">
              <div className="inner-pulse" />
            </div>
            <div className="window">
              <div className="inner-light" style={{ opacity: 0.4 + (audioLevel / 200) }} />
            </div>
          </div>
          {/* Webcam/Video Display */}
          <div className="webcam-display">
            {backendVideo ? (
              <img src={backendVideo} alt="Backend Video Stream" className="backend-video" />
            ) : (
              webcamActive ? (
                <>
                  <video ref={videoRef} className="webcam-video" autoPlay playsInline />
                  <canvas ref={canvasRef} width="320" height="240" className="hidden-canvas" />
                </>
              ) : (
                <div className="webcam-inactive">
                  <Video className="webcam-icon" />
                  <span className="webcam-text">Webcam inactive</span>
                </div>
              )
            )}
          </div>
          {/* Control Panel */}
          <div className="control-panel">
            <div className="knobs">
              <Knob name="PITCH" value={knobValues.freq} color="#10B981" />
              <Knob name="VOLUM" value={knobValues.resonance} color="#3B82F6" />
              <Knob name="DELAY" value={knobValues.delay} color="#EC4899" />
              <Knob name="REVERB" value={knobValues.reverb} color="#F59E0B" />
              <Knob name="PLAYBACK" value={knobValues.modulation} color="#8B5CF6" />
            </div>
            <div className="progress-bar">
              <div className="progress-indicator" style={{ width: `${audioLevel}%` }} />
            </div>
            <div className="button-group">
              <button onClick={backendVideo ? () => {} : startWebcamFallback} className={`btn ${webcamActive ? 'btn-red' : 'btn-teal'}`} title={webcamActive ? "Stop Webcam" : "Start Webcam"}>
                {webcamActive ? <Square size={24} /> : <Video size={24} />}
              </button>
              <button onClick={toggleSound} className={`btn ${isPlaying ? 'btn-yellow' : 'btn-green'}`} title={isPlaying ? "Pause Sound" : "Play Sound"}>
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>
              <button onClick={() => setGestureMode(!gestureMode)} className={`btn ${gestureMode ? 'btn-purple' : 'btn-gray'}`} title={gestureMode ? "Disable Hand Gesture Mode" : "Enable Hand Gesture Mode"}>
                <Hand size={24} />
              </button>
              <button onClick={() => setKnobValues({ freq: 90, resonance: 90, delay: 90, reverb: 90, modulation: 90 })} className="btn btn-blue" title="Reset Controls">
                <RefreshCw size={24} />
              </button>
            </div>
            {gestureMode && (
              <div className="gesture-indicator">
                <div className="gesture-text-title">Current Gesture</div>
                <div className="gesture-text-value">
                  {currentGesture === "pitch" 
                    ? `PITCH (${(pitchValue * 100).toFixed(0)}%)`
                    : currentGesture === "reverb" ? "REVERB" 
                      : currentGesture === "peace_up" ? "PEACE SIGN" 
                      : currentGesture === "open_hand" ? "OPEN HAND" 
                      : currentGesture === "closed_fist" ? "CLOSED FIST" 
                      : currentGesture === "neutral" ? "NEUTRAL" 
                      : "NO GESTURE"}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

export default Sono;
