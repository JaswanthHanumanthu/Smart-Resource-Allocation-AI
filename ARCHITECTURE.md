# 🛡️ Smart Resource Allocator: System Architecture

## 1. Tactical Mission Flow (The Data Pipeline)
The platform utilizes a **Three-Stage Verification Pipeline** to ensure field data integrity:
1.  **RAW_INPUT**: Unstructured field notes (Text/Image/Audio) are ingested.
2.  **AI_TRIAGE**: Gemini 1.5 Flash performs PII redaction, situational categorization, and 'Truth Checks' for spam detection.
3.  **VERIFIED_DATA**: Human administrators in the **Admin Portal** must manually authenticate flagged reports before they appear on public heatmaps or impact executive metrics.

## 2. Advanced AI Modeling
*   **Multimodal Ingestion**: Gemini 1.5 Flash processes tactical audio memos and situational photographs to estimate **Severity Scores (1-10)** and **Human Impact Counts**.
*   **Explainable UX (XUX)**: The Volunteer Matching Engine uses a **Radar Profile** to explain recommendation reasoning (Skill, Proximity, Availability).
*   **Temporal Projection**: The AI analyzes current clusters to predict **High-Probability Risk** sectors in the next 0-5 hours.

## 3. High-Performance Architecture
*   **Geospatial Resilience**: The dashboard uses a **Master-Detail Layout** in Streamlit, optimized with `st.cache_data` to handle 5,000+ data points with sub-1.5s situational updates.
*   **Offline-First (PWA)**: Implemented as a **Progressive Web App** using a Service Worker (`sw.js`) and IndexedDB-style sync queues, ensuring foundational UI remains accessible in zero-connectivity environments.

## 4. Security & Privacy Guardrails
*   **PII Redaction**: All raw field notes are automatically scrubbed for names and phone numbers using AI-driven NER (Named Entity Recognition).
*   **Anomaly Detection**: Real-time geospatial monitoring triggers alerts on sudden report spikes, preventing bot-driven data floods or botnet attacks.
*   **Rate Limiting**: Integrated per-user ingestion caps to ensure system availability during peak crisis periods.

---
*Status: Production Prototype v1.0 • Built for Humanitarian Resilience*
