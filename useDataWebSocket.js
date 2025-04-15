import { useState, useEffect } from "react";

const useDataWebSocket = () => {
  const [data, setData] = useState({ gesture: "neutral", pitch_value: 0 });

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/data");
    ws.onopen = () => {
      console.log("Data WebSocket connected");
    };
    ws.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      setData(newData);
    };
    ws.onerror = (error) => {
      console.error("Data WebSocket error:", error);
    };
    ws.onclose = () => {
      console.log("Data WebSocket disconnected");
    };

    return () => {
      ws.close();
    };
  }, []);

  return data;
};

export default useDataWebSocket;
