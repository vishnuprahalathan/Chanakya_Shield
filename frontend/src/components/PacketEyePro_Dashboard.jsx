import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  BarChart,
  Bar,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import "./Dashboard.css";

const COLORS = [
  "#00C49F",
  "#FFBB28",
  "#FF8042",
  "#0088FE",
  "#FF66CC",
  "#33CCFF",
  "#AA66FF",
];

// ✅ Map protocol numbers to protocol names
const PROTOCOL_MAP = {
  1: "ICMP",
  6: "TCP",
  17: "UDP",
  2: "IGMP",
  47: "GRE",
  50: "ESP",
  51: "AH",
  89: "OSPF",
};

const PacketEyePro_Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [protocolData, setProtocolData] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [attackData, setAttackData] = useState([]);
  const [darkMode, setDarkMode] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [summaryRes, protocolRes, timelineRes, attackRes] =
          await Promise.all([
            fetch("http://localhost:8080/api/packets/summary"),
            fetch("http://localhost:8080/api/packets/protocol-summary"),
            fetch("http://localhost:8080/api/packets/timeline"),
            fetch("http://localhost:8080/api/packets/attack-summary"),
          ]);

        const summaryJson = await summaryRes.json();
        const protocolJson = await protocolRes.json();
        const timelineJson = await timelineRes.json();
        const attackJson = await attackRes.json();

        setSummary(summaryJson);

        // ✅ Convert protocol numbers to names
        const mappedProtocolData = protocolJson.map((p) => ({
          ...p,
          protocol: PROTOCOL_MAP[p.protocol] || `Unknown (${p.protocol})`,
        }));

        setProtocolData(mappedProtocolData);
        setTimelineData(processTimeline(timelineJson));
        setAttackData(attackJson);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.error("❌ Error fetching dashboard data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const processTimeline = (data) => {
    const grouped = {};
    data.forEach((pkt) => {
      const t = pkt.timestamp?.split("T")[1]?.slice(0, 8) || pkt.timestamp;
      if (!grouped[t]) grouped[t] = { t, count: 0, anomalies: 0 };
      grouped[t].count += 1;
      if (pkt.status === "Anomaly") grouped[t].anomalies += 1;
    });
    return Object.values(grouped).reverse();
  };

  if (!summary)
    return (
      <div className="text-center mt-10 text-gray-500 text-lg">
        Loading Dashboard...
      </div>
    );

  return (
    <div className={`dashboard ${darkMode ? "dark" : "light"}`}>
      {/* HEADER */}
      <div className="dashboard-header">
        <h1>📊 CHANAKYA SHIELD — Live Network Dashboard</h1>
        <div className="header-controls">
          <p className="last-updated">Last Updated: {lastUpdated}</p>
          <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
            {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
          </button>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="kpi-container">
        <KpiCard label="Total Packets" value={summary.totalPackets} color="#007bff" />
        <KpiCard label="Normal" value={summary.normalPackets} color="#28a745" />
        <KpiCard label="Anomalies" value={summary.anomalyPackets} color="#ffc107" />
        <KpiCard label="Attacks" value={summary.totalAttacks} color="#dc3545" />
        <KpiCard
          label="Anomaly Rate (%)"
          value={`${summary.anomalyRate}%`}
          color="#6f42c1"
        />
      </div>

      {/* LINE CHART */}
      <div className="chart-container">
        <h2>📈 Traffic & Anomaly Timeline</h2>
        {timelineData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#007bff"
                name="Packets"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="anomalies"
                stroke="#dc3545"
                name="Anomalies"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No timeline data yet</p>
        )}
      </div>

      {/* 🌐 PROTOCOL PIE CHART */}
      <div className="chart-container">
        <h2>🌐 Protocol Distribution</h2>
        {protocolData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={protocolData}
                dataKey="count"
                nameKey="protocol"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={({ protocol, percent }) =>
                  `${protocol} (${(percent * 100).toFixed(1)}%)`
                } // ✅ Show protocol name + %
              >
                {protocolData.map((_, index) => (
                  <Cell
                    key={`cell-proto-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, name, entry) => [
                  `${value}`,
                  entry.payload.protocol,
                ]}
              />
              <Legend formatter={(value) => `${value}`} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No protocol data available</p>
        )}
      </div>

      {/* 🧠 ATTACK TYPE DISTRIBUTION */}
      <div className="chart-container">
        <h2>💀 Attack Type Distribution</h2>
        {attackData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={attackData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="attack" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#dc3545" name="Attack Count">
                {attackData.map((_, index) => (
                  <Cell
                    key={`cell-attack-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="no-data">No attack data available</p>
        )}
      </div>
    </div>
  );
};

const KpiCard = ({ label, value, color }) => (
  <div className="kpi-card" style={{ borderTop: `4px solid ${color}` }}>
    <h3>{label}</h3>
    <p style={{ color }}>{value}</p>
  </div>
);

export default PacketEyePro_Dashboard;
