import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import CONFIG from '../../config';
import './EvaluationDashboard.css';

const EvaluationDashboard = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [metrics, setMetrics] = useState({
        classical: { accuracy: 0, f1: 0, fpr: 0, fnr: 0, avg_confidence: 0, avg_latency: 0 },
        quantum: { accuracy: 0, f1: 0, fpr: 0, fnr: 0, avg_confidence: 0, avg_latency: 0 },
        packet_id: 0,
        explanation: "SYSTEM READY. Awaiting packet stream initialization...",
        attack_type: "N/A"
    });
    const [history, setHistory] = useState([]);
    const [packetStream, setPacketStream] = useState([]);
    const socketRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    const startEvaluation = async () => {
        setIsRunning(true);
        setMetrics(prev => ({ ...prev, explanation: "CORE INITIALIZED. Synchronizing with Quantum-Inspired engine..." }));

        const connect = async () => {
            if (!isRunning && socketRef.current) return; // Prevent loop if stopped manually

            try {
                await fetch(`${CONFIG.ML_SERVER_URL}/api/reset-eval`);
            } catch (err) {
                console.warn("Reset signal failed:", err);
            }

            const socket = new WebSocket(CONFIG.WS_EVAL_URL);
            socketRef.current = socket;

            socket.onopen = () => {
                setMetrics(prev => ({ ...prev, explanation: "UPLINK ESTABLISHED. Processing real-time telemetry..." }));
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.heartbeat || !data.classical) return;
                
                setMetrics(data);
                setHistory(prev => {
                    const newHistory = [...prev, {
                        id: data.packet_id,
                        q_acc: data.quantum.accuracy,
                        c_acc: data.classical.accuracy,
                        q_conf: data.quantum.avg_confidence,
                        c_conf: data.classical.avg_confidence
                    }];
                    return newHistory.slice(-50);
                });

                setPacketStream(prev => {
                    const newPacket = {
                        id: data.packet_id,
                        type: data.attack_type,
                        quantum: data.quantum.accuracy >= data.classical.accuracy,
                        timestamp: new Date().toLocaleTimeString()
                    };
                    return [newPacket, ...prev].slice(0, 10);
                });
            };

            socket.onerror = () => {
                setMetrics(prev => ({ ...prev, explanation: "UPLINK ERROR. Attempting reconnection..." }));
            };

            socket.onclose = () => {
                if (isRunning) {
                    reconnectTimeoutRef.current = setTimeout(connect, 3000); // Auto-reconnect in 3s
                }
            };
        };

        setHistory([]);
        setPacketStream([]);
        connect();
    };

    const stopEvaluation = () => {
        setIsRunning(false);
        if (socketRef.current) socketRef.current.close();
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        setMetrics(prev => ({ ...prev, explanation: "SYSTEM HALTED. Evaluation session terminated." }));
    };

    return (
        <div className="evaluation-dashboard">
            <header className="eval-header">
                <div className="header-left">
                    <h1>Real-Time Packet Evaluation</h1>
                    <p className="subtitle">Quantum-Inspired Advantage (QUBO Mapping) vs Classical SVM/RF Baseline</p>
                </div>
                <div className="status-badge">
                    <span className={isRunning ? "pulse green" : "dot red"}></span>
                    {isRunning ? "CORE ACTIVE" : "ENGINE STANDBY"}
                </div>
            </header>

            <div className="controls-section">
                <button
                    className={`btn-eval ${isRunning ? 'stop' : 'start'}`}
                    onClick={isRunning ? stopEvaluation : startEvaluation}
                >
                    {isRunning ? "ABORT EVALUATION" : "INITIATE ENGINE"}
                </button>
                <div className="disclaimer">
                    <span>⚡</span>
                    <p>Metrics computed packet-by-packet using <strong>Simulated Quantum Annealing</strong> heuristics.</p>
                </div>
            </div>

            <div className="panel-row">
                <div className="panel card">
                    <h3><span>📈</span> Detection Accuracy Delta</h3>
                    <div className="metric-comparison">
                        <div className="metric-box">
                            <h4>Classical</h4>
                            <div className="big-number">{(metrics.classical.accuracy || 0).toFixed(1)}%</div>
                            <div className="sub-metric">F1-Score: {(metrics.classical.f1 || 0).toFixed(2)}</div>
                        </div>
                        <div className="vs-divider">VS</div>
                        <div className="metric-box quantum">
                            <h4>Quantum-Inspired</h4>
                            <div className="big-number highlight">{(metrics.quantum.accuracy || 0).toFixed(1)}%</div>
                            <div className="sub-metric">F1-Score: {(metrics.quantum.f1 || 0).toFixed(2)}</div>
                        </div>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="colorQ" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3fb950" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#3fb950" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorC" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="id" hide />
                                <YAxis domain={[0, 100]} hide />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'rgba(5, 7, 10, 0.95)', borderRadius: '12px', border: '1px solid rgba(0, 212, 255, 0.2)', color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="c_acc" stroke="#8884d8" fillOpacity={1} fill="url(#colorC)" name="Classical" isAnimationActive={false} />
                                <Area type="monotone" dataKey="q_acc" stroke="#3fb950" strokeWidth={4} fillOpacity={1} fill="url(#colorQ)" name="Quantum-Inspired" isAnimationActive={false} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="panel card">
                    <h3><span>🛡️</span> Security Precision Analysis</h3>
                    <div className="fp-fn-grid">
                        <div className="stat-item">
                            <span>False Positive Rate (FPR)</span>
                            <div className="bar-wrapper">
                                <span className="bar-label">C</span>
                                <div className="bar-track"><div className="bar-fill classical" style={{ width: `${Math.min(100, (metrics.classical.fpr || 0))}%` }}></div></div>
                                <span className="val">{(metrics.classical.fpr || 0).toFixed(2)}%</span>
                            </div>
                            <div className="bar-wrapper">
                                <span className="bar-label">Q</span>
                                <div className="bar-track"><div className="bar-fill quantum" style={{ width: `${Math.min(100, (metrics.quantum.fpr || 0))}%` }}></div></div>
                                <span className="val">{(metrics.quantum.fpr || 0).toFixed(2)}%</span>
                            </div>
                        </div>

                        <div className="stat-item">
                            <span>False Negative Rate (FNR)</span>
                            <div className="bar-wrapper">
                                <span className="bar-label">C</span>
                                <div className="bar-track"><div className="bar-fill classical" style={{ width: `${Math.min(100, (metrics.classical.fnr || 0))}%` }}></div></div>
                                <span className="val">{(metrics.classical.fnr || 0).toFixed(2)}%</span>
                            </div>
                            <div className="bar-wrapper">
                                <span className="bar-label">Q</span>
                                <div className="bar-track"><div className="bar-fill quantum" style={{ width: `${Math.min(100, (metrics.quantum.fnr || 0))}%` }}></div></div>
                                <span className="val">{(metrics.quantum.fnr || 0).toFixed(2)}%</span>
                            </div>
                        </div>
                        <div className="improvement">
                            FNR Reduction: {metrics.classical.fnr > 0 || metrics.quantum.fnr > 0
                                ? `${((metrics.classical.fnr - metrics.quantum.fnr) >= 0 ? "+" : "")}${(metrics.classical.fnr - metrics.quantum.fnr).toFixed(2)}%`
                                : "Awaiting attack packets..."}
                        </div>
                    </div>
                </div>
            </div>

            <div className="panel-row">
                <div className="panel card">
                    <h3><span>🧠</span> Average Engine Confidence</h3>
                    <div className="metric-row">
                        <div>
                            <span>Classical Confidence</span>
                            <strong>{(metrics.classical.avg_confidence || 0).toFixed(4)}</strong>
                        </div>
                        <div>
                            <span>Quantum Enhancement</span>
                            <strong className="green-text">{(metrics.quantum.avg_confidence || 0).toFixed(4)}</strong>
                        </div>
                    </div>
                </div>

                <div className="panel card">
                    <h3><span>⚡</span> Computational Latency (ms)</h3>
                    <div className="tradeoff-box">
                        <div className="perf-item">
                            <div className="comparison">
                                <span className="c-val">{(metrics.classical.avg_latency || 0).toFixed(2)}</span>
                                <span className="arrow">→</span>
                                <span className="q-val warning">{(metrics.quantum.avg_latency || 0).toFixed(2)}</span>
                            </div>
                            <span>Avg Inference Time</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="panel full-width card terminal-panel">
                <div className="terminal-header">
                    <div className="t-dot red"></div>
                    <div className="t-dot yellow"></div>
                    <div className="t-dot green"></div>
                    <span className="t-title">XAI: Quantum Explainability Seed {metrics.packet_id}</span>
                </div>
                <div className="terminal-body">
                    <span className="prompt">$</span>
                    <span className="log-msg">{metrics.explanation}</span>
                </div>
            </div>

            {isRunning && (
                <div className="panel full-width card packet-stream-panel">
                    <h3><span>📡</span> Real-Time Packet Ingress</h3>
                    <div className="packet-grid">
                        <div className="packet-header">
                            <span>ID</span>
                            <span>TYPE</span>
                            <span>PIPELINE</span>
                            <span>TIMESTAMP</span>
                        </div>
                        {packetStream.map((p, i) => (
                            <div key={i} className={`packet-item ${p.type === 'BENIGN' ? 'benign' : 'attack'}`}>
                                <span className="p-id">#{p.id}</span>
                                <span className="p-type">{p.type}</span>
                                <span className="p-status">{p.quantum ? "Quantum-Optimized" : "Classical-Pass"}</span>
                                <span className="p-time">{p.timestamp}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="footer-constraints">
                <p>CHANAKYA SHIELD PRE-FLIGHT EVALUATION SYSTEM | V2.4.0-STABLE</p>
            </div>
        </div>
    );
};

export default EvaluationDashboard;
