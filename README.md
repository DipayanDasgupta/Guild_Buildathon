# Insure-Agent AI Backend | The Guild Buildathon

This repository contains the backend API for the "Insure-Agent AI" platform, a complete solution for **Problem Statement 2** of The Guild Buildathon. It is a robust Flask API deployed on Render, designed to automate and streamline tasks for insurance micro-entrepreneurs using an advanced, agentic AI pipeline.

**Live API URL:** [https://guild-buildathon.onrender.com](https://guild-buildathon.onrender.com)
**Live Frontend Application:** [https://guild-buildathon-frontend.vercel.app](https://guild-buildathon-frontend.vercel.app)

## ✨ Core Features

- **Smart AI Form Filler (`/api/documents/process`):**
  - The core AI engine. It accepts PDF/image uploads of KYC documents or policy forms.
  - Implements a two-stage AI pipeline:
    1.  **Text & Image Extraction:** Uses `PyMuPDF` for PDF text and `Tesseract OCR` for image text. It also extracts the primary photo from KYC documents.
    2.  **Advanced Analysis:** Sends extracted text to the Gemini AI API with an "expert agent" prompt to identify the document type, extract all relevant data into a structured JSON, and determine missing documents.
  - Returns a rich JSON object to the frontend to pre-fill the client onboarding form.

- **Full Client CRM (`/api/clients`):**
  - A complete, data-driven REST API for client management with full CRUD (Create, Read, Update, Delete) functionality.
  - Supports advanced filtering by client status (`Active`, `Engaged`, `Prospective`) and searching by name or policy ID.

- **Automatic Reconciliation Engine (`/api/reconciliation`):**
  - An intelligent tool that accepts PDF uploads of bank statements and policy logs.
  - Uses a powerful Gemini prompt to perform AI-driven "fuzzy matching" on transaction data, identifying pairs and flagging exceptions for the agent.

- **Dynamic Dashboard Endpoints (`/api/dashboard`):**
  - Provides real-time, aggregated data from the database to power the frontend dashboard, including monthly conversions, today's follow-ups, and policies nearing renewal.

## 🛠️ Tech Stack & Architecture

- **Framework:** Flask (using Application Factory Pattern)
- **Deployment:** Render
- **Database:** PostgreSQL on Render, managed with SQLAlchemy
- **Database Migrations:** Flask-Migrate & Alembic
- **Dependency Management:** Poetry
- **AI / Machine Learning:**
  - **Google Gemini API (`gemini-1.5-flash-latest`):** For all text analysis, data extraction, and fuzzy matching.
  - **PyMuPDF & Tesseract:** For robust text and image extraction from documents.

