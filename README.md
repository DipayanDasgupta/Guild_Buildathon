# Micro-Automator API Backend

This is the backend for the "InsureAgent" dashboard, a submission for **Problem Statement 2** of The Guild Buildathon. It's a robust Flask API deployed on Render, designed to automate and streamline tasks for insurance micro-entrepreneurs.

**Live API URL:** [https://guild-buildathon.onrender.com](https://guild-buildathon.onrender.com)

## ✨ Features

- **Intelligent Document Processing:** An API endpoint (`/api/documents/process`) that accepts PDF and image files.
- **Two-Stage AI Pipeline:**
  1.  Extracts text from PDFs (`PyMuPDF`) or images (OCR via `pytesseract`).
  2.  Sends only the extracted text to the Gemini AI API for analysis, saving costs and quota.
- **Database Integration:** Connected to a live PostgreSQL database on Render, managed with SQLAlchemy.
- **Health Checks:** Includes endpoints (`/` and `/api/db-health-check`) to monitor the status of the API and its database connection.

## 🛠️ Tech Stack

- **Framework:** Flask
- **Deployment:** Render
- **Database:** PostgreSQL (via SQLAlchemy)
- **Dependency Management:** Poetry
- **AI / Machine Learning:**
  - Google Gemini API (`gemini-1.5-flash`) for text analysis.
  - PyMuPDF for PDF text extraction.
  - Tesseract (via pytesseract) for Optical Character Recognition (OCR).

## �� Getting Started Locally

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation) for package management.
- The Tesseract OCR engine. (On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`)

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
    The API will be available at `http://127.0.0.1:5000`.

