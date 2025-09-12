# Micro-Automator: The Guild Buildathon (Problem Statement 2)

This repository contains the backend code for a tech-driven solution to empower micro-entrepreneurs by automating repetitive tasks, as outlined in PS2 of The Guild Buildathon.

The backend is built with **Flask** and designed for easy, one-click deployment on **Render**. The frontend should be built with **Anvil**.

## Features (API Endpoints)

-   **/api/documents/process**: `POST` - Accepts a document file for AI-powered data extraction.
-   **/api/automation/send_reminder**: `POST` - Sends automated reminders.
-   More endpoints for payment automation, workflow management, etc., can be added following the same Blueprint pattern.

---

## 🚀 Getting Started: Replicate This Project

Follow these steps to get your own version of this application running in minutes.

### Prerequisites

-   Python 3.10+
-   [uv](https://github.com/astral-sh/uv): An extremely fast Python package installer.
    -   `pip install uv` (or `brew install uv`, etc.)

### Step 1: Set Up The Anvil Frontend

1.  **Create Anvil App**: Go to [anvil.works](https://anvil.works) and create a new application.
2.  **Get Uplink Key**: In your new Anvil app, go to **Settings (⚙️) > Uplink** and click **Enable the Anvil Server Uplink**. Copy the key.

### Step 2: Set Up The Backend Locally

1.  **Clone this repository (if you haven't already):**
    ```bash
    git clone https://github.com/DipayanDasgupta/Guild_Buildathon.git
    cd Guild_Buildathon
    ```

2.  **Create Environment & Install Dependencies:**
    `uv` makes this a simple two-step process.
    ```bash
    # Create a virtual environment named .venv
    uv venv

    # Install all dependencies from pyproject.toml
    uv pip install -e ".[dev]"
    ```

3.  **Configure Environment Variables:**
    Create a file named `.env` in the root directory and add your secrets:
    ```.env
    # Paste the key from Anvil here
    ANVIL_UPLINK_KEY="your-anvil-uplink-key-goes-here"

    # For local development, this URL is correct
    BACKEND_URL="http://127.0.0.1:5000"
    ```

4.  **Run the Backend & Uplink:**
    You'll need two separate terminals for this.

    -   **Terminal 1: Run the Flask App**
        ```bash
        source .venv/bin/activate # On Windows: .venv\Scripts\activate
        flask run
        ```
        Your backend is now running at `http://127.0.0.1:5000`.

    -   **Terminal 2: Run the Anvil Uplink**
        ```bash
        source .venv/bin/activate
        python src/micro_automator/uplink.py
        ```
        This script securely connects your Anvil frontend to your local backend. You can now test the full application!

### Step 3: Deploy to Production

1.  **Commit and Push to GitHub**:
    ```bash
    git add .
    git commit -m "feat: Initial project structure and code"
    git push origin main
    ```

2.  **Deploy Backend to Render**:
    -   Go to [Render.com](https://render.com) and create a new **Blueprint Service**.
    -   Connect the GitHub repository. Render will automatically detect the `render.yaml` file and configure everything.
    -   Click **Approve**.
    -   Under the **Environment** tab for your new service, add your `ANVIL_UPLINK_KEY` as a secret environment variable.
    -   Render will deploy your app and give you a public URL (e.g., `https://micro-automator-backend.onrender.com`).

3.  **Connect Live Frontend to Live Backend**:
    -   Update your Anvil app's code to use the live Render URL when making HTTP requests.
    -   **Publish** your Anvil app.

**Congratulations! Your entire application is now live.**
