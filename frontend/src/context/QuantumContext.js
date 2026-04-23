import React, { createContext, useEffect, useState } from "react";
import CONFIG from "../config";

export const QuantumContext = createContext();

export const QuantumProvider = ({ children }) => {
  const [quantum, setQuantum] = useState({
    enabled: false,
    mode: "Classical",
    features: [],
  });

  useEffect(() => {
    fetch(`${CONFIG.BACKEND_URL}/api/system/status`)
      .then(res => res.json())
      .then(data => {
        setQuantum({
          enabled: data.quantumEnabled,
          mode: data.mode,
          features: data.selectedFeatures || [],
        });
      })
      .catch(() => {
        setQuantum({
          enabled: false,
          mode: "Classical (Fallback)",
          features: [],
        });
      });
  }, []);

  return (
    <QuantumContext.Provider value={quantum}>
      {children}
    </QuantumContext.Provider>
  );
};
