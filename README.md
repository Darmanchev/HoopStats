# 🏀 HoopStats (NBA Analytics Platform)

![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

A comprehensive analytical platform for basketball (NBA) statistics with built-in Machine Learning modules to predict match outcomes.

## 💡 About the Project

HoopStats bridges the gap between data collection, analysis, and user-friendly visualization. It is a full-stack solution that pulls real-time statistics from external APIs (NBA, ESPN), processes them, and delivers in-depth analytics: ranging from standings and player metrics to predicting the win probabilities of upcoming games using trained ML models.

## 🚀 Architecture and Development Stages

### 1. Backend (Python + FastAPI)
- **API & Database:** RESTful API built with FastAPI, managing the database via SQLAlchemy and Alembic migrations.
- **Data Integration:** Custom API clients (`services/clients/espn.py`, `nba.py`) designed for automated parsing of schedules, results, and injury reports.
- **Machine Learning:** Integrated ML models (`model.joblib` / `scikit-learn`) capable of forecasting the outcome of future matches based on historical team performance metrics.

### 2. Frontend (React + TypeScript)
- **Interface:** A smooth Single Page Application (SPA) powered by React and Vite.
- **Dashboards:** Interactive and engaging widgets (LiveGameStats, Standings, TeamEfficiency, Predictions).
- **Design:** Implements modern UI patterns, featuring a Theme Toggle, robust charting, and detailed player cards.

### 3. Infrastructure
- **Docker Compose:** Streamlined launching of the database, backend, and frontend environments with a single command.

## ⚙️ Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Darmanchev/HoopStats.git
   cd HoopStats
   ```
2. Prepare your `.env` files (you can copy the provided `.env.example`).
3. Run the project via Docker:
   ```bash
   docker-compose up -d
   ```
4. For the initial setup, run migrations and seed the database with historical data:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python backend/seed.py
   ```

---
*Built for those who love basketball and appreciate deep data analytics.* 🏆
