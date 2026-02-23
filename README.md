# 🌍 Enterprise Maps Scraper & Dashboard

A full-stack automation system that extracts business data from Google Maps and streams it into a live dashboard with real-time Google Sheets integration.

---

## 📌 Overview

This project automates business data extraction from Google Maps using asynchronous scraping techniques and displays the processed results in a structured dashboard.

It is designed for:

- Lead generation
- Market research
- Competitor analysis
- Business intelligence automation

The system supports real-time Google Sheets streaming and scalable scraping architecture.

---

## 🚀 Key Features

- 🕷 Async Google Maps Scraper (Playwright-based)
- 📊 Live Dashboard (Frontend + Backend)
- 📄 CSV Export Support
- 📈 Real-time Google Sheets Integration
- 🐳 Dockerized Deployment
- ⚡ Optimized Async Architecture
- 🧱 Clean Backend–Frontend Separation

---

## 🏗 Architecture
Google Maps
↓
Async Playwright Scraper (Python)
↓
Data Processing Layer
↓
CSV / Google Sheets
↓
Backend API
↓
Frontend Dashboard


---

## 🛠 Tech Stack

**Backend**
- Python
- Async Playwright
- FastAPI / Custom API
- Docker

**Frontend**
- JavaScript
- Dashboard UI

**Data Handling**
- CSV processing
- Google Sheets API


---

## ⚙ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/rakshdevstudio/maps.git
cd maps
pip install -r requirements.txt
python scraper.py
npm install
npm run dev
docker-compose up --build
