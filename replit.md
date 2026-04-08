# Smart Resource Allocator PRO v2.0

An AI-driven mission control dashboard for NGOs and humanitarian organizations.

## Overview

Facilitates the digitization of field reports (handwritten notes, voice memos, images), prioritizes community needs using AI (Google Gemini 1.5 Flash), and matches them with available volunteers based on skills, urgency, and proximity.

## Tech Stack

- **Language:** Python 3.12
- **Framework:** Streamlit
- **AI Backend:** Google Gemini 1.5 Flash (`google-generativeai`)
- **Data:** pandas, numpy
- **Visualization:** plotly, folium, streamlit-folium
- **Validation:** pydantic
- **Port:** 5000 (0.0.0.0)

## Project Structure

- `app.py` — Main Streamlit app entry point
- `src/` — Core logic and components
  - `components/dashboard.py` — Dashboard UI components
  - `models/schemas.py` — Data schemas
  - `models/matching.py` — Volunteer matching engine
  - `utils/` — Helpers: deduplication, fairness auditing, logging, PDF generation, security/PII redaction
  - `processor.py` — AI data processing orchestration
  - `styles.css` — Custom styling
- `scripts/` — Utility scripts (data generation, integrity reports)
- `data/mock_needs.csv` — Sample needs data
- `static/` — PWA assets (manifest, service worker)

## Running the App

```bash
streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
```

## Configuration

- **API Key:** Set `GOOGLE_API_KEY` in Streamlit Secrets or as an environment variable. The app runs in simulation mode without it.
- If no secrets file is present, the app gracefully falls back to simulation mode.

## Deployment

Configured for autoscale deployment via Replit. Run command:
```
streamlit run app.py --server.port 5000 --server.address 0.0.0.0 --server.headless true
```
