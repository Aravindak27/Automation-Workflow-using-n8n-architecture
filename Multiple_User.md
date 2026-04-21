# Multi-Tenant (SaaS) Architecture Guide

This document outlines the complete process for onboarding new users (coworkers, clients, or separate companies) into your AI Email Automation system. 

The architecture is built around a **Single Master Google Sheet** and **Isolated n8n Workflows**. This ensures user data remains strictly segregated while keeping backend maintenance at zero.

---

## Step 1: The Master Google Sheet Setup

All clients across all your users are stored in ONE centralized Google Sheet (in the "clients" tab). To ensure the AI knows which client belongs to which user, we filter horizontally using a strict column identity.

**Required Columns:**
Ensure your Google Sheet includes these specific columns alongside your standard ones (`priority`, `domains`, etc.):
- `user_name` (e.g., Aravind)
- `user_id` (e.g., U-001)
- **`user_mail`** (e.g., `aravind2005ak@gmail.com`) ⬅️ *CRITICAL FIELD*

When a new user wants to use your system, simply add their clients as new rows to this sheet, making sure to copy/paste the new user's exact email address into the `user_mail` column for all of their rows.

---

## Step 2: Creating the Master n8n Workflow

Before adding new users, you must have a perfectly functioning "Master Workflow" for yourself.

1. **Trigger Node**: Add a `Gmail Trigger` (or IMAP). Authenticate it with your personal email account.
2. **HTTP Request Node** (The AI Engine):
   - **Method**: `POST`
   - **URL**: `http://localhost:5000/process-email`
   - **Send Body**: Enabled
   - **JSON Body**:
     ```json
     {
       "tenant_id": "aravind2005ak@gmail.com",
       "from": "{{ $json.from.address }}",
       "subject": "{{ $json.subject }}",
       "body": "{{ $json.textPlain }}"
     }
     ```
     *(The Python API will strictly mathematical filter the Google Sheet so it ONLY matches against clients containing `aravind2005ak@gmail.com`)*
3. **If Node**: Proceed only if `{{ $json.matched }} Is True`.
4. **Telegram Node**: Add your Telegram Bot and set the text to `{{ $json.telegram_message }}`. Set Parse Mode to `HTML`.

---

## Step 3: Onboarding a New User (Duplication Method)

When someone new signs up, do **not** run their emails through your personal workflow. Keep their credentials separate so you can activate/deactivate them instantly.

1. **Duplicate**: In your n8n dashboard, click the three dots on your "Master Workflow" and click **Duplicate**. Rename it (e.g., "AI Agent - AravindJan").
2. **Re-Authenticate Trigger**: Open the `Gmail Trigger` node and connect it to the new user's email credentials (e.g., `aravindjan2005@gmail.com`).
3. **Update the tenant_id**: Open the `HTTP Request` node. Change the `"tenant_id"` inside the JSON to exactly match the email address you put into the `user_mail` column of the Google Sheet for this user.
     ```json
     {
       "tenant_id": "aravindjan2005@gmail.com",
       ...
     }
     ```
4. **Update End Destination**: If this new user has their own Telegram chat or Slack where they want alerts routed, update the Telegram node to point to their Chat ID.

---

## Step 4: Activating The Weekly Report

The Python API tracks all emails implicitly via an internal SQLite database (`stats.db`). It automatically records which `tenant_id` triggered the email.

**To auto-send them a weekly stats breakdown:**
1. Create a quick two-step workflow in n8n.
2. **Trigger**: `Schedule Trigger` node. Set it to run every Monday at 10:00 AM.
3. **HTTP Request Node**:
   - Method: `GET`
   - URL: `http://localhost:5000/weekly-report/aravindjan2005@gmail.com`
4. **Telegram Node**: Send `{{ $json.telegram_message }}` to that user.

---

### 🛡 Benefits of this architecture:
- **Zero Coding Needed:** The python code never needs to be updated. Just add rows to Excel and duplicate n8n logic blocks.
- **Fail-safe isolation:** If one user's email inbox disconnects, it will never break another user's automation.
- **Scaleable Pricing:** If someone stops paying for your service, you simply toggle "Deactivate" on their specific n8n workflow.
