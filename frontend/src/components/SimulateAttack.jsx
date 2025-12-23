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
        console.error("Error fetching simulation status:", err);
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
      // alert(text); // Basic alert removed for better UX
      setIsRunning(true);
      // navigate("/packets"); // Stay on page to see status
    } catch (err) {
      console.error("Failed to start simulation:", err);
    } finally {
      setIsStarting(false);
    }
  };

  const stopSimulation = async () => {
    setIsStopping(true);
    try {
      const res = await fetch("http://localhost:8080/api/stop-simulation");
      setIsRunning(false);
    } catch (err) {
      console.error("Failed to stop simulation:", err);
    } finally {
      setIsStopping(false);
    }
  };

  return (
    <div className="simulate-container">
      <h2>THREAT SIMULATION</h2>
      <p>
        Initiate controlled cyber attacks using the CICIDS2017 replay engine.
      </p>

      <div className="control-panel">
        <div className="simulate-buttons">
          <button
            className="simulate-btn start"
            onClick={startSimulation}
            disabled={isStarting || isRunning}
          >
            {isStarting ? "INITIALIZING..." : "INITIATE ATTACK"}
          </button>

          <button
            className="simulate-btn stop"
            onClick={stopSimulation}
            disabled={!isRunning || isStopping}
          >
            {isStopping ? "TERMINATING..." : "ABORT"}
          </button>
        </div>

        <div className="terminal-status">
          <span className="terminal-line typing-cursor">
            STATUS: {isRunning ? "SIMULATION ACTIVE - GENERATING TRAFFIC..." : "SYSTEM STANDBY - READY"}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SimulateAttack;