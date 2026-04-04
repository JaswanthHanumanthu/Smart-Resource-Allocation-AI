# 🛡️ Smart Resource Allocator: AI-Driven Humanitarian Resilience

A high-fidelity, professional-grade mission control dashboard for NGOs to manage community needs, volunteer matching, and crisis forecasting. Built for **speed, privacy, and field resilience**.
Link :- https://jaswanthhanumanthu-smart-resource-allocation-app-i2k7ts.streamlit.app/

[![Live Demo](https://img.shields.io/badge/Demo-Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit)](https://smart-resource-allocator.streamlit.app/)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-blue?style=for-the-badge&logo=google-gemini)](https://ai.google.dev/)
[![Privacy First](https://img.shields.io/badge/Privacy-PII%20Redacted-green?style=for-the-badge)](https://github.com/JaswanthHanumanthu/Smart-Resource-Allocation#%EF%B8%8F-ethical-ai-usage--data-privacy)

---

## 🌟 Key Pillars

### 1. 📂 Zero-Friction Digitization (Multimodal AI)
Erase the bottleneck of manual data entry. Field teams can upload **handwritten paper surveys, voice memos, or situational photos**. Our **Gemini 1.5 Flash** pipeline automatically:
*   **Transcribes** audio reports into structured data.
*   **Digitizes** messy field notes and paper forms.
*   **Analyzes** photographs to estimate severity and human impact.

### 2. 📡 Field-First Resilience (PWA & Offline)
Designed for crisis zones with intermittent connectivity.
*   **Offline Queue**: Reports are captured locally and synced automatically when a connection is restored.
*   **PWA Support**: Install the dashboard on mobile devices for native-like performance in the field.
*   **Lightweight UI**: Bento-Grid Glassmorphism interface optimized for sub-1.5s situational updates.

### 3. ⚖️ Ethical AI & Privacy-First
*   **PII Redaction**: Automatic scrubbing of names, phone numbers, and IDs before any data is stored.
*   **Human-In-The-Loop**: All AI-extracted reports go through a **Secure Admin Portal** for manual verification.
*   **Fairness Auditing**: Real-time parity scores to ensure resources are allocated without bias across different demographics and sectors.

---

## 🚀 Core Features

*   **🎯 Smart Matching Engine**: Prioritizes Urgency, Skill, and Proximity to connect the right volunteers to the most critical needs.
*   **🔮 Temporal Crisis Forecasting**: AI analyzes current clusters to predict "High-Probability Risk" areas 0-5 hours into the future.
*   **📊 Executive Impact Analytics**: Real-time Plotly dashboards for stakeholder reporting, tracking "Total Humans Impacted" and "Resource Parity."
*   **🗺️ Interactive Impact Map**: Geospatial visualization with Heatmaps, Marker Clusters, and Dependency Mapping (e.g., *Clear Debris* must happen before *Food Delivery*).
*   **🗨️ Chat with your Data**: Natural language interface for NGO managers to query the resource database.

---

## 🛠️ Technical Stack

*   **Frontend/App**: [Streamlit](https://streamlit.io/) (Python)
*   **AI Backend**: [Google Gemini 1.5 Flash](https://ai.google.dev/)
*   **Visualization**: [Folium](https://python-visualization.github.io/folium/), [Plotly](https://plotly.com/), [Lucide](https://lucide.dev/)
*   **Data Science**: [Pandas](https://pandas.pydata.org/), [Pydantic](https://docs.pydantic.dev/)
*   **Deployment**: PWA (Service Worker + Manifest)

---

## 🚦 Quick Start

### 1. Prerequisites
*   Python 3.10+
*   [Google AI Studio API Key](https://aistudio.google.com/)

### 2. Setup Environment
Clone the repository and create a `.env` file:
```bash
git clone https://github.com/JaswanthHanumanthu/Smart-Resource-Allocation.git
cd Smart-Resource-Allocation
cp .env.example .env
```
Add your Gemini API key to `.env`:
```env
GEMINI_API_KEY=your_gemini_key_here
```

### 3. Installation
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📐 System Architecture
The platform utilizes a **Three-Stage Verification Pipeline**:
1.  **RAW_INPUT**: Unstructured field notes (Text/Image/Audio) are ingested.
2.  **AI_TRIAGE**: Gemini performs PII redaction and 'Truth Checks'.
3.  **VERIFIED_DATA**: Human administrators authenticate reports before they impact live metrics.

For more technical details, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 🤝 Contributing
We welcome contributions to help build more resilient communities. Please see our contribution guidelines for how to get involved.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built with ❤️ for Humanitarian Impact • Production Prototype v2.0*
