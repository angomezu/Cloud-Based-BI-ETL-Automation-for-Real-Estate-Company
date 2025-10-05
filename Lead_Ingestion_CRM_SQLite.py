import requests
import sqlite3
import time
from datetime import datetime
import pytz

# API and DB config
API_KEY = 'API KEY'
URL = 'URL'
DB_FILE = r'C:\sqlite\database.db'
HEADERS = {
    'X-API-KEY': API_KEY,
    'Accept': 'application/json'
}
LIMIT = 100

# Timezone handling
crm_timezone = pytz.timezone('insert your time zone here')

def convert_to_crm_timezone(utc_datetime_str):
    if not utc_datetime_str:
        return None
    
    # Try parsing full timestamp first
    try:
        utc_dt = datetime.strptime(utc_datetime_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        try:
            # Try parsing simple date format
            utc_dt = datetime.strptime(utc_datetime_str, "%Y-%m-%d")
        except ValueError:
            print(f"Unrecognized date format: {utc_datetime_str}")
            return None
    
    # Set timezone info
    utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    crm_dt = utc_dt.astimezone(crm_timezone)
    return crm_dt.strftime("%Y-%m-%d %H:%M:%S")

# Date range for API request
start_date = '2018-01-01T00:00:00.000Z'
end_date = '2025-12-31T23:59:59.999Z'
date_range_type = 'creation'
offset = 0
all_leads = []

# Fetch data from API
while True:
    params = {
        'limit': LIMIT,
        'offset': offset,
        'start_date': start_date,
        'end_date': end_date,
        'date_range_type': date_range_type
    }
    response = requests.get(URL, headers=HEADERS, params=params)
    if response.status_code != 200:
        print("Error al consultar la API:", response.status_code, response.text)
        break
    leads = response.json()
    print(f"Offset {offset}: {len(leads)} leads")
    if not leads:
        break
    all_leads.extend(leads)
    offset += LIMIT
    time.sleep(0.2)

print(f"Total de leads traídos: {len(all_leads)}")

# Save data to SQLite
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Make sure table exists
cur.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY,
        title TEXT,
        pipeline TEXT,
        step TEXT,
        step_id INTEGER,
        status TEXT,
        amount REAL,
        probability REAL,
        currency TEXT,
        starred BOOLEAN,
        remind_date TEXT,
        remind_time TEXT,
        next_action_at TEXT,
        created_at TEXT,
        estimated_closing_date TEXT,
        updated_at TEXT,
        description TEXT,
        html_description TEXT,
        tags TEXT,
        created_from TEXT,
        closed_at TEXT,
        attachment_count INTEGER,
        created_by_id INTEGER,
        user_id INTEGER,
        client_folder_id INTEGER,
        client_folder_name TEXT,
        team_id INTEGER,
        team_name TEXT
    )
''')

# Insert data
for lead in all_leads:
    tags_str = ",".join(lead.get("tags", [])) if lead.get("tags") else None
    data = (
        lead.get("id"),
        lead.get("title"),
        lead.get("pipeline"),
        lead.get("step"),
        lead.get("step_id"),
        lead.get("status"),
        lead.get("amount"),
        lead.get("probability"),
        lead.get("currency"),
        int(lead.get("starred", False)) if lead.get("starred") is not None else None,
        lead.get("remind_date"),
        lead.get("remind_time"),
        convert_to_crm_timezone(lead.get("next_action_at")),
        convert_to_crm_timezone(lead.get("created_at")),
        lead.get("estimated_closing_date"),
        convert_to_crm_timezone(lead.get("updated_at")),
        lead.get("description"),
        lead.get("html_description"),
        tags_str,
        lead.get("created_from"),
        convert_to_crm_timezone(lead.get("closed_at")),
        lead.get("attachment_count"),
        lead.get("created_by_id"),
        lead.get("user_id"),
        lead.get("client_folder_id"),
        lead.get("client_folder_name"),
        lead.get("team_id"),
        lead.get("team_name"),
    )
    cur.execute('''
        INSERT OR REPLACE INTO leads (
            id, title, pipeline, step, step_id, status, amount, probability, currency, starred,
            remind_date, remind_time, next_action_at, created_at, estimated_closing_date, updated_at,
            description, html_description, tags, created_from, closed_at, attachment_count, created_by_id,
            user_id, client_folder_id, client_folder_name, team_id, team_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

conn.commit()
conn.close()
print("Process completed.")
