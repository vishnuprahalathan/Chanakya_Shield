# 🚀 PacketEye Pro - Deployment Guide (Free Hosting)

This guide explains how to host the **PacketEye Pro** stack for free while maintaining high performance.

## 🏗️ Architecture Overview
1. **Frontend (React):** Hosted on **Vercel** or **Netlify**.
2. **Backend (Spring Boot):** Hosted on **Railway** (Trial) or **Render** (Free Instance).
3. **ML Service (FastAPI):** Hosted on **Render** (Free Python Instance).
4. **Database (MySQL):** Hosted on **Aiven** (Free MySQL Plan).

---

## 1. Database (Aiven)
- Create a free account at [aiven.io](https://aiven.io/).
- Launch a free **MySQL** instance.
- Copy the `Service URI` and credentials.
- Update your `application.properties` or use environment variables in the backend deployment.

## 2. ML Service (Render)
- Link your GitHub repo to [Render.com](https://render.com/).
- Create a **Web Service**.
- Select the `mlmodel` directory.
- Use `Runtime: Python 3` and **Build Command:** `pip install -r requirements.txt`.
- **Start Command:** `python evaluation_server.py`.
- Render's free tier "sleeps" after inactivity. The auto-reconnect logic I added to the frontend will handle this gracefully.

## 3. Backend Service (Spring Boot)
- Similar to the ML service, create a **Web Service** on Render or Railway.
- Use the **Dockerfile** provided in the `/backend` folder.
- Set environment variables for the Aiven MySQL database:
  - `SPRING_DATASOURCE_URL`
  - `SPRING_DATASOURCE_USERNAME`
  - `SPRING_DATASOURCE_PASSWORD`

## 4. Frontend (Vercel)
- Push your code to GitHub.
- Import the project into [Vercel](https://vercel.com/).
- Vercel will automatically detect the React app in the `frontend` folder.
- **IMPORTANT:** Update the API URLs in your React components to point to your new Render/Railway URLs instead of `localhost`.

---

## 🛠️ Local Production Test
Before deploying, you can test the entire "Solid" stack locally using Docker:
```bash
docker-compose up --build
```
This will start MySQL, the Spring backend, and the ML service in sync.
