import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./SimulateAttack.css";

const SimulateAttack = () => {
  const navigate = useNavigate();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [isRunning, setIsRunning] = useState(false);

  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("http://localhost:8080/api/status");
        const data = await res.json();
        
        setIsRunning(data.simulation && data.simulation.includes("Running"));
      } catch (err) {
        console.error("⚠️ Error fetching simulation status:", err);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);


  const startSimulation = async () => {
    setIsStarting(true);
    try {
      const res = await fetch("http://localhost:8080/api/simulate-attack");
      const text = await res.text();
      alert(text);


      setIsRunning(true);
      navigate("/packets");
    } catch (err) {
      console.error("⚠️ Failed to start simulation:", err);
      alert("❌ Could not start simulation!");
    } finally {
      setIsStarting(false);
    }
  };

  const stopSimulation = async () => {
    setIsStopping(true);
    try {
      const res = await fetch("http://localhost:8080/api/stop-simulation");
      const text = await res.text();
      alert(text);
      setIsRunning(false);
    } catch (err) {
      console.error("⚠️ Failed to stop simulation:", err);
      alert("❌ Could not stop simulation!");
    } finally {
      setIsStopping(false);
    }
  };

  return (
    <div className="simulate-container">
      <h2>💣 Attack Simulation</h2>
      <p>
        Run CICIDS2017 replay script to simulate network attacks and observe real-time packet analysis.
      </p>

      <div className="simulate-buttons">
        <button
          className="simulate-btn start"
          onClick={startSimulation}
          disabled={isStarting || isRunning}
        >
          {isStarting ? "⏳ Starting..." : "▶️ Start Simulation"}
        </button>

        <button
          className="simulate-btn stop"
          onClick={stopSimulation}
          disabled={!isRunning || isStopping}
        >
          {isStopping ? "⏳ Stopping..." : "🛑 Stop Simulation"}
        </button>
      </div>

      <div className="simulate-status">
        Status:{" "}
        <span className={isRunning ? "status-running" : "status-stopped"}>
          {isRunning ? "🟢 Running" : "🔴 Stopped"}
        </span>
      </div>
    </div>
  );
};

export default SimulateAttack;
