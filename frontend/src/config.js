const CONFIG = {
    BACKEND_URL: process.env.REACT_APP_BACKEND_URL || "http://localhost:8080",
    ML_SERVER_URL: process.env.REACT_APP_ML_SERVER_URL || "http://localhost:8001",
    WS_EVAL_URL: process.env.REACT_APP_WS_EVAL_URL || "ws://localhost:8001/ws/evaluation"
};

export default CONFIG;
