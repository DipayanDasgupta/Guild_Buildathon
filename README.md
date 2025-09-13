# Micro-Automator API Backend | The Guild Buildathon

This repository contains the backend API for the "InsureAgent" dashboard, a complete solution for **Problem Statement 2** of The Guild Buildathon. It is a robust Flask API deployed on Render, designed to automate and streamline tasks for insurance micro-entrepreneurs using an advanced AI pipeline.

**Live API URL:** [https://guild-buildathon.onrender.com](https://guild-buildathon.onrender.com)
**Live Frontend Application:** [https://guild-buildathon-frontend.vercel.app](https://guild-buildathon-frontend.vercel.app)

## ✨ Core Features

- **Intelligent Document Processing (`/api/documents/process`):**
  - Accepts PDF and image file uploads.
  - Implements a two-stage AI pipeline to conserve API quota and increase efficiency.
    1.  **Text Extraction:** Uses `PyMuPDF` for PDFs and Tesseract OCR for images.
    2.  **Advanced Analysis:** Sends extracted text to the Gemini AI API for deep analysis.
- **AI-Powered Analytics:**
  - Extracts key data points (policy number, customer name, etc.).
  - Generates a concise summary of the document.
  - Categorizes the document (e.g., "New Policy", "Claim Form").
  - Determines the document's sentiment ("Urgent", "Positive", etc.).
  - Creates a list of actionable items for the agent.
- **Database Integration:**
  - All AI-generated analytics and document metadata are saved to a live PostgreSQL database hosted on Render.
  - Uses SQLAlchemy for robust data modeling.
- **Dashboard Data Endpoints:**
  - Provides mock endpoints (`/api/dashboard/*`, `/api/clients`) to populate the frontend with realistic data for statistics, quick actions, and product listings.
- **Health Checks:**
  - Includes `/` and `/api/db-health-check` to monitor the live status of the API and its database connection.

## 🛠️ Tech Stack & Architecture

- **Framework:** Flask (using Application Factory Pattern to prevent circular imports)
- **Deployment:** Render
- **Database:** PostgreSQL on Render, managed with SQLAlchemy
- **Dependency Management:** Poetry
- **AI / Machine Learning:**
  - **Google Gemini API (`gemini-1.5-flash-latest`):** For all text analysis and generation.
  - **PyMuPDF:** For high-performance PDF text extraction.
  - **Tesseract (via `pytesseract`):** For Optical Character Recognition (OCR) on images.

## 🚀 Getting Started Locally

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- The Tesseract OCR engine (On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DipayanDasgupta/Guild_Buildathon.git
    cd Guild_Buildathon
    ```

2.  **Install dependencies:**
    ```bash
    poetry install --no-root
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your secrets:
    ```.env
    # Your connection string from Render (must start with postgresql://)
    DATABASE_URL="postgresql://user:password@host/database"

    # Your API key from Google AI Studio
    GOOGLE_API_KEY="your-gemini-api-key"
    ```

4.  **Run the application:**
    ```bash
    flask run
    ```
    The API will be available at `http://1227.0.0.1:5000`.

