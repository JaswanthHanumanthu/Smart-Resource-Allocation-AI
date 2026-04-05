# 🏗️ Smart Resource Allocation: System Architecture

This document outlines the high-level architecture and design decisions behind the **Smart Resource Allocation** dashboard—a state-of-the-art AI triage system for humanitarian relief.

## 🔄 1. Operational Data Flow

The platform handles unstructured mission data (messy notes, audio, photos) and transforms them into actionable geospatial intelligence.

```mermaid
graph TD
    A[User Input: Notes/Photos/Audio] --> B[Streamlit UI]
    B --> C{Gemini 1.5 Flash AI}
    C -->|Multimodal Extraction| D[Structured JSON Schema]
    D --> E[Data Processing Layer & Validation]
    E --> F[In-Memory Session Database]
    F --> G[Interactive Folium Map Visualization]
    F --> H[Executive Impact Analytics]
    F --> I[AI Matching Engine & Dispatch]
```

1.  **Ingestion (UI)**: Field reports are uploaded via the "Data Upload" portal.
2.  **Multimodal Analysis (Gemini)**: Raw data is sent to **Gemini 1.5 Flash**. The AI performs OCR, translation, and sentiment analysis to extract urgency, category, and coordinates.
3.  **Refinement (Processing)**: Extracted data is validated in a "Review Queue" before entering the mission-critical database.
4.  **Operationalization (Visuals/Matching)**: Data is dynamically rendered on a **Folium Heatmap** and passed to a **Heuristic + AI Matching Engine** to pair volunteers with tasks.

---

## 🛠️ 2. Tech Stack Rationale

### **Frontend & Logic: Streamlit**
*   **Rapid Prototyping**: We prioritized development speed for the hackathon environment. Streamlit allows us to build a responsive, data-driven UI entirely in Python.
*   **State Management**: Native session state handling allows for real-time reactivity without complex React/Vue setups.

### **AI Core: Google Gemini 1.5 Flash**
*   **Multimodal Excellence**: Unlike traditional OCR, Gemini handles messy handwriting, field audio, and scene analysis simultaneously.
*   **Exceptional Window**: The large context window allows us to pass entire CSV datasets for "Chat with your Data" and "Executive Summary" features.
*   **XAI (Explainable AI)**: We use Gemini to generate natural language "Reasoning Statements" for every volunteer match, ensuring transparency in dispatch decisions.

### **Visuals: Folium & Plotly**
*   **Folium**: Chosen for its robust Python integration and ability to handle complex geospatial data with standard tile sets (DarkMatter/Positron).
*   **Plotly**: Provides interactive, theme-aware analytics that inherit the application's glassmorphism aesthetic.

---

## 🚀 3. Scalability Roadmap (1,000,000+ Reports)

To transition from a hackathon prototype to a global humanitarian standard, the following infrastructure upgrades would be implemented:

### **Database Migration**
*   **Current**: Sequential Python Pandas DataFrames (Session State).
*   **Target**: **PostgreSQL with PostGIS**. This would provide high-performance spatial queries and robust ACID compliance for managing millions of mission records.

### **Distributed Processing**
*   **Asynchronous Tasks**: Use **Celery + Redis** to move AI extraction (Gemini calls) into background workers. This prevents UI blocking during mass ingestion events.
*   **Load Balancing**: Deploy the containerized application (Docker) behind an **NGINX Load Balancer** on a Kubernetes (GKE) cluster to handle traffic spikes.

### **Cache Strategy**
*   Implement **Redis Caching** for frequently viewed map clusters and executive analytics, reducing redundant API hits and improving latency for NGO managers.

---

## 🛡️ 4. Global Exception Shield

The application implements a **Defensive Architecture** to ensure zero-downtime during field operations:
*   **Global Exception Wrapper**: A high-level shield catches unanticipated failures, logs them to a remote logger, and shows a "High Traffic" status to the user instead of a crash.
*   **Heuristic Fallbacks**: If the Gemini API is unreachable, the system automatically falls back to spatial heuristics for clustering and matching, ensuring mission continuity in low-connectivity zones.
