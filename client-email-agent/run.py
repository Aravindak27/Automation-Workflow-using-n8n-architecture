import json
import os
from dotenv import load_dotenv
from groq import Groq
from agent import client_email_agent
from sheets import load_clients_from_sheet, match_client

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def run_agent(email_from, email_subject, email_body):

    print("\n" + "="*50)
    print("LOADING CLIENT LIST FROM GOOGLE SHEETS...")
    print("="*50)

    clients = load_clients_from_sheet()
    print(f"Loaded {len(clients)} clients.")
    for c in clients:
        print(f"  - {c['name']} ({c['priority']})")

    print("\nMATCHING EMAIL AGAINST CLIENT LIST...")
    matched_client, keyword_hit = match_client(
        email_from, email_subject, email_body, clients
    )

    if not matched_client:
        print("\n⚠️  No matching client found. Email skipped.")
        return

    print(f"✅ Matched: {matched_client['name']}")
    print(f"   Priority : {matched_client['priority']}")
    print(f"   SLA      : {matched_client['sla_hours']} hours")
    print(f"   Keyword  : {keyword_hit or 'domain match'}")

    user_message = f"""
Process this incoming client email:

Client Name: {matched_client['name']}
Client Priority Tier: {matched_client['priority']}
SLA: {matched_client['sla_hours']} hours
Keyword matched: {keyword_hit or 'none'}
From: {email_from}
Subject: {email_subject}

Email Body:
{email_body}
"""

    print("\nSENDING TO AI AGENT...")
    print("-"*50)

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": client_email_agent.instruction
            },
            {
                "role": "user",
                "content": user_message
            }
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

    try:
        parsed = json.loads(raw)

        print("\nAGENT RESPONSE:")
        print(json.dumps(parsed, indent=2))

        print("\n--- DRAFT REPLY PREVIEW ---")
        print(parsed["draft_reply"])
        print(f"\nPriority Score : {parsed['priority_score']}/10")
        print(f"Urgency        : {parsed['classification']['urgency'].upper()}")
        print(f"Summary        : {parsed['classification']['summary']}")
        print(f"SLA Deadline   : Reply within {matched_client['sla_hours']} hours")

    except Exception as e:
        print("Raw response:\n", raw)
        print(f"\nParse error: {e}")


# --- Test 1: Known client email ---
print("\n🧪 TEST 1: Known client (ABC Constructions)")
run_agent(
    email_from="ceo@abc.com",
    email_subject="Contract Proposal - Need Sign-off Today",
    email_body="""Hi Aravind,
Our legal team needs your sign-off by end of day today.
This is quite urgent for us.
Regards, Rajesh Kumar"""
)

# --- Test 2: Unknown sender ---
print("\n🧪 TEST 2: Unknown sender (should be skipped)")
run_agent(
    email_from="someone@random.com",
    email_subject="Hello",
    email_body="Just reaching out randomly."
)