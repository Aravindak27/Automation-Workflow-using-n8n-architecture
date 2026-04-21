import json
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from groq import Groq
from agent import client_email_agent
from sheets import load_clients_from_sheet, match_client

load_dotenv()

app = Flask(__name__)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Agent is running"})


@app.route("/process-email", methods=["POST"])
def process_email():
    data = request.json

    # --- Validate incoming payload ---
    required = ["from", "subject", "body"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    email_from    = data["from"]
    email_subject = data["subject"]
    email_body    = data["body"]
    email_id      = data.get("email_id", "unknown")

    print(f"\n{'='*50}")
    print(f"NEW EMAIL RECEIVED")
    print(f"From    : {email_from}")
    print(f"Subject : {email_subject}")
    print(f"{'='*50}")

    # --- Load client list and match ---
    try:
        clients = load_clients_from_sheet()
    except Exception as e:
        return jsonify({"error": f"Failed to load client list: {str(e)}"}), 500

    matched_client, keyword_hit = match_client(
        email_from, email_subject, email_body, clients
    )

    if not matched_client:
        print("⚠️  Not a client email — ignored.")
        return jsonify({
            "matched": False,
            "message": "Sender not in client list. Email ignored."
        }), 200

    print(f"✅ Matched: {matched_client['name']} ({matched_client['priority']})")

    # --- Build prompt and call AI agent ---
    user_message = f"""
Process this incoming client email:

Client Name: {matched_client['name']}
Client Priority Tier: {matched_client['priority']}
SLA: {matched_client['sla_hours']} hours
Keyword matched: {keyword_hit or 'domain match'}
From: {email_from}
Subject: {email_subject}

Email Body:
{email_body}
"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": client_email_agent.instruction},
                {"role": "user",   "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)

    except Exception as e:
        return jsonify({"error": f"AI agent failed: {str(e)}"}), 500

    # --- Build final response for n8n ---
    result = {
        "matched": True,
        "email_id": email_id,
        "received_at": datetime.utcnow().isoformat() + "Z",
        "client": {
            "name":      matched_client["name"],
            "priority":  matched_client["priority"],
            "sla_hours": matched_client["sla_hours"]
        },
        "keyword_hit":    keyword_hit,
        "classification": parsed["classification"],
        "priority_score": parsed["priority_score"],
        "priority_reason": parsed["priority_reason"],
        "draft_reply":    parsed["draft_reply"],
        "sla_deadline":   f"Reply within {matched_client['sla_hours']} hours"
    }

    print(f"Priority Score : {parsed['priority_score']}/10")
    print(f"Urgency        : {parsed['classification']['urgency'].upper()}")
    print(f"Draft ready    : ✅")

    return jsonify(result), 200


if __name__ == "__main__":
    print("🚀 Client Email Intelligence API running on http://localhost:5000")
    app.run(debug=True, port=5000)