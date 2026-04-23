import React, { useEffect, useState } from "react";
import CONFIG from "../config";
import "./PacketsTable.css";

const PacketsTable = () => {
  const [packets, setPackets] = useState([]);
  const [isStopping, setIsStopping] = useState(false);
  const [isStopped, setIsStopped] = useState(false); // ✅ new state to track stop status

  useEffect(() => {
    const fetchPackets = async () => {
      try {
        const res = await fetch(`${CONFIG.BACKEND_URL}/api/packets`);
        const data = await res.json();
        setPackets(data);
      } catch (err) {
        console.error("Error fetching packets:", err);
      }
    };

    // only fetch if not stopped
    if (!isStopped) {
      fetchPackets();
      const interval = setInterval(fetchPackets, 3000);
      return () => clearInterval(interval);
    }
  }, [isStopped]);

  const stopCapture = async () => {
    setIsStopping(true);
    try {
      const res = await fetch(`${CONFIG.BACKEND_URL}/api/stop-capture`);
      const text = await res.text();
      alert(text);
      setIsStopped(true); // ✅ mark capture as stopped
    } catch (err) {
      alert("⚠️ Failed to stop packet capture!");
      console.error("Stop capture error:", err);
    } finally {
      setIsStopping(false);
    }
  };

  return (
    <div className="packets-container">
      <div className="header-row">
        <h2>📡 Captured Packets</h2>
        <button
          className={`stop-btn ${isStopped ? "stopped" : ""}`}
          onClick={stopCapture}
          disabled={isStopping || isStopped}
        >
          {isStopped
            ? "✅ Stopped"
            : isStopping
            ? "⏳ Stopping..."
            : "🛑 Stop Packet Capture"}
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Timestamp</th>
            <th>Source IP</th>
            <th>Destination IP</th>
            <th>Protocol</th>
            <th>Length</th>
            <th>Status</th>
            <th>Attack Type</th>
          </tr>
        </thead>
        <tbody>
          {packets.map((pkt, i) => (
            <tr key={i} className={pkt.status === "Anomaly" ? "anomaly" : ""}>
              <td>{i + 1}</td>
              <td>{pkt.timestamp}</td>
              <td>{pkt.srcIp}</td>
              <td>{pkt.destIp}</td>
              <td>{pkt.protocol}</td>
              <td>{pkt.length}</td>
              <td>{pkt.status}</td>
              <td>{pkt.attackType || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PacketsTable;