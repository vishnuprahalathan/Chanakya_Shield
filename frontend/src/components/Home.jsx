import React from "react";
import { useNavigate } from "react-router-dom";
import CONFIG from "../config";
import "./Home.css";

const Home = () => {
  const navigate = useNavigate();

  const startCapture = async () => {
    try {
      const res = await fetch(`${CONFIG.BACKEND_URL}/api/start-capture`);
      const text = await res.text();
      alert(text);
      navigate("/packets"); 
    } catch (err) {
      alert("⚠️ Unable to start analysis script!");
      console.error(err);
    }
  };

  return (
    <div className="home-container">
      <h1 className="title">⚔️ Chanakya Shield</h1>
      <p className="subtitle"> Real-Time Network Threat Detection</p>

      <div className="features">
        <div className="feature">📡 Real-time Packet Capture</div>
        <div className="feature">🧠 ML-based Anomaly Detection</div>
        <div className="feature">💣 Attack Simulation</div>
        <div className="feature">📲 Telegram Alerts</div>
      </div>

      <button className="start-btn" onClick={startCapture}>
        🚀 Start Packet Capture
      </button>
    </div>
  );
};

export default Home;
