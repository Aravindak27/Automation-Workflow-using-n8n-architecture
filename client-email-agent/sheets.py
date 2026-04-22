import os
import csv
import io
import urllib.request


def load_clients_from_sheet(tenant_email):
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=clients"

    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8-sig")

    # Strip spaces from ALL header names before parsing
    reader = csv.DictReader(io.StringIO(content))
    reader.fieldnames = [h.strip() for h in reader.fieldnames]

    clients = []
    for row in reader:
        row_user_mail = row.get("user_mail", "").strip().lower()
        if row_user_mail != tenant_email.lower():
            continue
            
        clients.append({
            "client_id":  row.get("client_id", "").strip(),
            "user_name":  row.get("user_name", "").strip(),
            "user_id":    row.get("user_id", "").strip(),
            "user_mail":  row_user_mail,
            "name":       row["name"].strip(),
            "priority":   row["priority"].strip().lower(),
            "domains":    [d.strip() for d in row["domains"].split(",")],
            "emails":     [e.strip() for e in row["emails"].split(",")],
            "keywords":   [k.strip() for k in row["keywords"].split(",")],
            "sla_hours":  int(row["sla_hours"].strip())
        })

    return clients


def match_client(email_from, email_subject, email_body, clients):
    email_from_lower  = email_from.lower()
    subject_lower     = email_subject.lower()
    body_lower        = email_body.lower()

    # PASS 1: Explicit Email Address Match (Highest Priority)
    for client in clients:
        email_match = any(
            e.strip().lower() in email_from_lower
            for e in client["emails"] if e.strip()
        )
        if email_match:
            keyword_hit = next(
                (k for k in client["keywords"]
                 if k.strip() and (k.lower() in subject_lower or k.lower() in body_lower)),
                None
            )
            return client, keyword_hit

    # PASS 2: Domain Match Fallback
    for client in clients:
        domain_match = any(
            d.strip().lower() in email_from_lower
            for d in client["domains"] if d.strip()
        )
        if domain_match:
            keyword_hit = next(
                (k for k in client["keywords"]
                 if k.strip() and (k.lower() in subject_lower or k.lower() in body_lower)),
                None
            )
            return client, keyword_hit

    return None, None