---
title: Email API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# Automation Workflow using n8n and AI Agent

This repository contains an automated email classification and processing workflow. It uses **n8n** for orchestrating the workflow (reading incoming emails, handling responses) and a **Flask-based Python API** integrated with Groq Cloud for AI email processing (reading intent, fetching matching client SLA priority from Google Sheets, drafting an email response).

---

## 🛠 Prerequisites

1. **Python 3.x** installed.
2. **Node.js & npm** installed (to run n8n, unless using Docker).
3. **Groq API Key** and Google Sheets credentials configured.

---

## 🚀 1. Starting the Python AI Server

The Python server (`API.PY`) handles the AI logic, evaluating inbound messages against a Google Sheet client list and using Groq to build intelligent drafts.

1. **Open a terminal/command prompt.**
2. **Navigate to the python directory:**
   ```bash
   cd client-email-agent
   ```
3. **Install Dependencies** (if you haven't already):
   ```bash
   pip install flask python-dotenv groq google-auth google-api-python-client
   ```
4. **Environment Variables**:
   Ensure you have configured your `.env` file inside `client-email-agent/` with the required keys (e.g., `GROQ_API_KEY`).
5. **Start the API server**:
   ```bash
   python API.PY
   ```
   *You should see output indicating that the Flask server is running locally on port 5000 (`http://localhost:5000` or `http://127.0.0.1:5000`). Keep this terminal open.*

---

## ⚙️ 2. Starting n8n Local Workflow

n8n is the automation engine that will listen to your email inbox, send the email data over to your Python API, and execute subsequent steps based on the API response.

1. **Open a second terminal window.**
2. **Start n8n**:
   ```bash
   npx n8n start
   ```
   *(Alternatively, if installed globally, you can just run `n8n`).*
3. **Access the Dashboard**:
   Open a web browser and navigate to `http://localhost:5678`.
4. **Activate the Workflow**:
   Inside your n8n workspace, make sure the workflow containing your email triggers and HTTP request node is set to **Active**.

---

## 🔗 How They Connect (n8n HTTP Request Node)

The core mechanism of this automation relies on n8n talking to your local Python API. 

In your **n8n HTTP Request node**:
- **Method**: `POST`
- **URL**: `http://localhost:5000/process-email` (or `http://host.docker.internal:5000/process-email` if running n8n via Docker)
- **Send Body**: Enabled
- **Body Content** (JSON Example):
  ```json
  {
    "tenant_id": "aravind2005ak@gmail.com",
    "from": "{{ $json.from }}",
    "subject": "{{ $json.subject }}",
    "body": "{{ $json.textPlain }}"
  }
  ```

Once triggered, n8n sends the email object to the Python Server. Python evaluates it with Groq and returns a JSON payload including variables like `draft_reply`, `priority_score`, and `matched` (boolean). Further n8n nodes can read this resulting JSON and action it!

---

## 💡 Troubleshooting

- **Connection Error / Connection Refused in n8n**: Your Python server is down. Check the terminal running `python API.PY` to ensure it hasn't crashed or stopped.
- **Python Console UnicodeEncodeErrors (Windows)**: If you accidentally print emojis to a Command Prompt or PowerShell in Windows without explicit encoding set to `utf-8`, it can crash the API. We've removed emojis from `.py` code to run safely out-of-the-box on Windows.
- **Missing Module in Python**: Simply run `pip install <module_name>`.
