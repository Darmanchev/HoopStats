# 🏀 HoopStats (NBA Analytics Platform)

![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Комплексная аналитическая платформа для баскетбольной статистики (NBA) со встроенными модулями машинного обучения (Machine Learning) для прогнозирования результатов матчей.

## 💡 О проекте

HoopStats объединяет в себе сбор данных, их анализ и удобное отображение для пользователя. Это полностек-решение, которое в реальном времени подтягивает статистику из внешних API (NBA, ESPN), обрабатывает ее и выдает аналитику: от турнирных таблиц и показателей игроков до вероятности победы команд в грядущих матчах, используя обученные ML-модели.

## 🚀 Архитектура и этапы создания

### 1. Backend (Python + FastAPI)
- **API & База Данных:** REST API на FastAPI, работа с базой через SQLAlchemy + миграции Alembic.
- **Интеграция данных:** Написаны клиенты (`services/clients/espn.py`, `nba.py`) для автоматического парсинга расписаний, результатов и травм.
- **Machine Learning:** Интегрированная ML-модель (`model.joblib` / `scikit-learn`), которая предсказывает исход будущих матчей на основе исторических метрик команд.

### 2. Frontend (React + TypeScript)
- **Интерфейс:** SPA (Single Page Application) на React + Vite.
- **Дашборды:** Реализованы интерактивные виджеты (LiveGameStats, Standings, TeamEfficiency, Predictions).
- **Дизайн:** Использование современных UI-паттернов, Theme Toggle, графики и карточки игроков.

### 3. Инфраструктура
- **Docker Compose:** Легкий запуск базы данных, бэкенда и фронтенда одной командой.

## ⚙️ Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Darmanchev/HoopStats.git
   cd HoopStats
   ```
2. Подготовьте `.env` файлы (можно скопировать из `.env.example`).
3. Запустите проект через Docker:
   ```bash
   docker-compose up -d
   ```
4. Для первого запуска выполните миграции и сидирование (заполнение) БД историческими данными:
   ```bash
   docker-compose exec backend alembic upgrade head
   docker-compose exec backend python backend/seed.py
   ```

---
*Создано для тех, кто любит баскетбол и ценит глубокую аналитику данных.* 🏆
