from flask import Flask, request, jsonify
import psycopg2
from psycopg2 import sql
import os
from datetime import datetime
import json

app = Flask(__name__)

# DB connection details from environment variables
DB_PARAMS = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASS'),
    'host': os.environ.get('DB_HOST'),
    'port': int(os.environ.get('DB_PORT', 5432))
}

# Whitelist of allowed account names to prevent SQL injection
ALLOWED_ACCOUNTS = {'office_a', 'office_b', 'office_c'}


def _get_client_folder(data: dict):
    """
    Return (id, name) from 'client_folder' (docs) or 'client' (your live payload).
    """
    if not isinstance(data, dict):
        return None, None
    cf = data.get('client_folder') or data.get('client') or {}
    if isinstance(cf, dict):
        return cf.get('id'), cf.get('name')
    return None, None


def insert_lead_step_changed(data, event_meta, account):
    """Inserts data into the correct account's step_changed table."""
    table_name = f"{account}_step_changed"
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    query = sql.SQL("""
        INSERT INTO {} (
            id, event, signature, has_succeeded, try_count, last_returned_code,
            received_at, lead_id, lead_title, lead_status, lead_step, lead_amount,
            lead_created_at, lead_updated_at, lead_user_email, lead_permalink,
            step_id, pipeline, created_at_utc, updated_at_utc, moved_by, raw_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """).format(sql.Identifier(table_name))

    cur.execute(query, (
        event_meta['id'], event_meta['event'], event_meta['signature'],
        event_meta['has_succeeded'], event_meta['try_count'], event_meta['last_returned_code'],
        datetime.utcnow(), data.get('id'), data.get(
            'title'), data.get('status'), data.get('step'),
        data.get('amount'), data.get('created_at'), data.get('updated_at'),
        (data.get('user') or {}).get('email'), data.get(
            'permalink'), data.get('step_id'),
        data.get('pipeline'), data.get('created_at'), data.get('updated_at'),
        (data.get('user') or {}).get('email'),
        json.dumps({'webhook_event': {**event_meta, 'data': data}})
    ))
    conn.commit()
    cur.close()
    conn.close()


def insert_lead_created(data, event_meta, account):
    """Inserts data into the correct account's lead_created table."""
    table_name = f"{account}_lead_created"
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    cf_id, cf_name = _get_client_folder(data)

    query = sql.SQL("""
        INSERT INTO {} (
            id, event, signature, has_succeeded, try_count, last_returned_code,
            received_at, lead_id, title, status, step, amount,
            created_at_utc, updated_at_utc, user_email, permalink,
            client_folder_id, client_folder_name, raw_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """).format(sql.Identifier(table_name))

    cur.execute(query, (
        event_meta['id'], event_meta['event'], event_meta['signature'],
        event_meta['has_succeeded'], event_meta['try_count'], event_meta['last_returned_code'],
        datetime.utcnow(), data.get('id'), data.get('title'), data.get('status'),
        data.get('step'), data.get('amount'),
        data.get('created_at'), data.get('updated_at'),
        (data.get('user') or {}).get('email'), data.get('permalink'),
        cf_id, cf_name,
        json.dumps({'webhook_event': {**event_meta, 'data': data}})
    ))
    conn.commit()
    cur.close()
    conn.close()


def insert_lead_deleted(data, event_meta, account):
    """Inserts data into the correct account's lead_deleted table."""
    table_name = f"{account}_lead_deleted"
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    query = sql.SQL("""
        INSERT INTO {} (
            id, event, signature, has_succeeded, try_count, last_returned_code,
            received_at, lead_id, title, deleted_at_utc, user_email, permalink, raw_data
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """).format(sql.Identifier(table_name))

    cur.execute(query, (
        event_meta['id'], event_meta['event'], event_meta['signature'],
        event_meta['has_succeeded'], event_meta['try_count'], event_meta['last_returned_code'],
        datetime.utcnow(), data.get('id'), data.get('title'), data.get('updated_at'),
        (data.get('user') or {}).get('email'), data.get('permalink'),
        json.dumps({'webhook_event': {**event_meta, 'data': data}})
    ))
    conn.commit()
    cur.close()
    conn.close()


def insert_client_folder_created(data, event_meta, account):
    """Inserts data into the correct account's client_folder_created table."""
    table_name = f"{account}_client_folder_created"
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    query = sql.SQL("""
        INSERT INTO {} (
            id, event, signature, has_succeeded, try_count, last_returned_code,
            received_at, folder_id, folder_name, created_at_utc, raw_data
        ) OVERRIDING SYSTEM VALUE VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """).format(sql.Identifier(table_name))

    cur.execute(query, (
        event_meta['id'], event_meta['event'], event_meta['signature'],
        event_meta['has_succeeded'], event_meta['try_count'], event_meta['last_returned_code'],
        datetime.utcnow(), data.get('id'), data.get('name'), data.get('created_at'),
        json.dumps({'webhook_event': {**event_meta, 'data': data}})
    ))
    conn.commit()
    cur.close()
    conn.close()


@app.route("/webhook/<account>", methods=["POST"])
def webhook(account):
    """Handles incoming webhooks for different accounts."""
    if account not in ALLOWED_ACCOUNTS:
        return jsonify({"error": "Invalid account"}), 400

    if not request.is_json:
        return jsonify({"error": "Invalid content type"}), 400

    full_payload = request.get_json()
    payload = full_payload.get("webhook_event", {})
    event = payload.get("event")
    data = payload.get("data", {})

    try:
        if event == "lead.step.changed":
            insert_lead_step_changed(data, payload, account)
        elif event == "lead.creation":
            insert_lead_created(data, payload, account)
        elif event == "lead.deleted":
            insert_lead_deleted(data, payload, account)
        elif event == "client_folder.created":
            insert_client_folder_created(data, payload, account)
        else:
            print(f"[{account.upper()}][UNHANDLED EVENT] {event}")

        return jsonify({"status": "success", "account": account, "event": event}), 200
    except Exception as e:
        print(
            f"Error processing webhook for account '{account}' and event '{event}': {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
