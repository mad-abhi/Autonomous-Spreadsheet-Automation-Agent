```markdown
⚡ GridPilot (Autonomous Spreadsheet Automation Agent)

An autonomous AI Agent built to orchestrate end-to-end spreadsheet workflows. The agent accepts natural language commands to synthesize structured datasets, format and style them locally in **Microsoft Excel**, synchronize them with **Google Sheets**, and publish shareable links—all driven by dynamic tool selection and Gemini reasoning.

---

 ✨ Features

-  Autonomous Tool Calling:** Uses **Gemini 3.6 Flash** to plan execution sequences, generate synthetic domain data, invoke local COM automation, and handle API retries with backoff.
-  Native Excel COM Automation:** Hooks directly into Windows Excel via `pywin32` to apply typography (Segoe UI), executive navy headers, alternating zebra striping, borders, and currency formatting.
-  Google Sheets & Drive API Integration:** Generates cloud spreadsheets, replicates executive styling, and sets Drive share permissions.
-  Glassmorphic Web Dashboard:** Real-time dark-mode UI with live WebSocket logs, interactive data preview table, multi-step progress indicators, and instant click-to-open links.

---

 🏗️ Architecture & Project Structure


spreadsheet-agent/
│
├── backend/
│   ├── main.py              # FastAPI server & WebSocket broadcaster
│   ├── agent.py             # Gemini reasoning loop & tool definitions
│   └── tools/
│       ├── excel_com.py     # Local Windows Excel COM automation
│       └── gsheets.py       # Google Sheets & Drive API integration
│
├── frontend/
│   ├── index.html           # Dark-mode glassmorphic control center
│   └── app.js               # WebSocket stream client & UI updater
│
├── output/                  # Generated .xlsx workbooks
├── .env                     # API keys (Gemini)
├── credentials.json         # Google OAuth Desktop client credentials
├── requirements.txt         # Python dependencies
└── run.bat                  # One-click startup script

```

---

## 📋 Prerequisites

* **OS:** Windows 10/11 *(required for local Microsoft Excel COM automation)*
* **Python:** Version 3.11 or 3.12+
* **Office:** Microsoft Excel installed locally
* **Google Cloud:** A GCP Project with **Google Sheets API** and **Google Drive API** enabled

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/gridpilot.git](https://github.com/your-username/gridpilot.git)
cd gridpilot/spreadsheet-agent

```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the `spreadsheet-agent/` directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here

```

### 5. Configure Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable both **Google Sheets API** and **Google Drive API**.
3. Under **APIs & Services > Audience**, configure the OAuth Consent Screen and add your Google email under **Test Users**.
4. Under **APIs & Services > Credentials**, create an **OAuth client ID** (Application Type: *Desktop App*).
5. Download the JSON key, rename it to `credentials.json`, and place it in the `spreadsheet-agent/` root folder.

---

## 💻 Running the Application

### Option 1: Quick Start (Windows)

Double-click `run.bat` or run:

```bat
run.bat

```

### Option 2: Manual Start

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

```

Open your browser at **`http://127.0.0.1:8000`**.

---

## 🎯 Example Prompts

Try entering any of the following instructions in the dashboard:

* *"Create a quarterly sales performance report with 5 regional reps, style in Excel and upload to Google Sheets."*
* *"Generate an employee directory with 6 employees across Engineering and Marketing, and export to Excel."*
* *"Build a marketing campaign budget with 4 channels, format numbers as currency, and sync to Google Sheets."*

---
