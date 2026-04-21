import os
import csv
import io
import urllib.request


def load_clients_from_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=clients"

    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8-sig")

    # Strip spaces from ALL header names before parsing
    reader = csv.DictReader(io.StringIO(content))
    reader.fieldnames = [h.strip() for h in reader.fieldnames]

    clients = []
    for row in reader:
        clients.append({
            "client_id":  row["client_id"].strip(),
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

    for client in clients:
        domain_match = any(
            d.lower() in email_from_lower
            for d in client["domains"]
        )
        email_match = any(
            e.lower() == email_from_lower
            for e in client["emails"]
        )
        keyword_hit = next(
            (k for k in client["keywords"]
             if k.lower() in subject_lower or k.lower() in body_lower),
            None
        )

        if domain_match or email_match:
            return client, keyword_hit

    return None, None