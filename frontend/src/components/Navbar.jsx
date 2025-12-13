import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import "./Navbar.css";

const Navbar = () => {
  const [darkMode, setDarkMode] = useState(() => {
   
    return localStorage.getItem("theme") === "dark";
  });


  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-theme");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.classList.remove("dark-theme");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  return (
    <nav className={`navbar ${darkMode ? "dark" : "light"}`}>
      <div className="logo">⚔️ Chanakya Shield</div>

      <ul>
        <li><Link to="/">Home</Link></li>
        <li><Link to="/packets">Packets Captured</Link></li>
        <li><Link to="/dashboard">Dashboard</Link></li>
        <li><Link to="/simulate">Simulate Attack</Link></li>
        <li><Link to="/alerts">Telegram Alerts</Link></li>
      </ul>

      {/* 🌗 Theme Toggle Button */}
      <button
        className="theme-toggle-btn"
        onClick={() => setDarkMode(!darkMode)}
      >
        {darkMode ? "☀️ Light" : "🌙 Dark"}
      </button>
    </nav>
  );
};

export default Navbar;
