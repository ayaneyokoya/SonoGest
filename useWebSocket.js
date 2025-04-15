// src/useWebSocket.js
import { useEffect, useRef } from 'react';

const useWebSocket = (onMessageCallback) => {
  const ws = useRef(null);

  useEffect(() => {
    // Connect to WebSocket server
    ws.current = new WebSocket("ws://localhost:8000/ws");

    ws.current.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Message from backend:", data);
      if (onMessageCallback) onMessageCallback(data);
    };

    ws.current.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.current.onclose = () => {
      console.log("WebSocket disconnected");
    };

    return () => {
      ws.current.close();
    };
  }, [onMessageCallback]);

  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { sendMessage };
};

export default useWebSocket;
