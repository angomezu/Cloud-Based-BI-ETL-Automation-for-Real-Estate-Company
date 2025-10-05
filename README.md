# Cloud-Based-BI-ETL-Automation-for-Real-Estate-Company

This project showcases a full-stack, cloud-native Business Intelligence platform built for SOC FIINBRO. It completely replaced a manual, Excel-based reporting workflow with a fully automated system that provides real-time analytics from the noCRM.io API into interactive Power BI dashboards.

## Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [System Architecture](#system-architecture)
- [Core Components](#core-components)
  - [1. ETL & API Synchronization](#1-etl--api-synchronization)
  - [2. Real-Time Webhook Ingestion](#2-real-time-webhook-ingestion)
  - [3. Database Schema & Data Model](#3-database-schema--data-model)
  - [4. Power BI Implementation](#4-power-bi-implementation)
- [Deployment on Render](#deployment-on-render)
- [Contact](#contact)

## About The Project

The primary goal of this project was to eliminate manual data exports and empower FIINBRO's executive team with reliable, near real-time KPIs. The solution involved architecting a data pipeline that captures CRM data through two methods: a daily incremental API sync and real-time webhook ingestion for critical events.

All data is stored in a cloud-hosted PostgreSQL database on Render, which serves as the single source of truth for a suite of 8 interactive Power BI dashboards.

**Business Impact:**
* **Eliminated Manual Work:** Replaced hours of weekly work spent on consolidating Excel exports.
* **Real-Time Visibility:** Executives now have live insights into sales performance, conversion rates, and pipeline health.
* **Improved Data Reliability:** Created a trusted, centralized data source, ensuring consistent KPIs across all reports.
* **Enhanced Traceability:** Every key CRM event is captured and stored for full auditability.

## Key Features

- **8 Interactive Power BI Dashboards:** Covering sales performance, pipeline tracking, executive activity, conversion rates, and monthly trends.
- **Fully Automated Cloud ETL:** Python scripts run on a daily schedule to incrementally sync new and updated lead data from the noCRM.io API.
- **Real-Time Event Ingestion:** A Flask webhook service instantly captures critical events like `lead.creation`, `lead.deleted`, and `lead.status.changed`.
- **Cloud-Hosted Database:** A robust PostgreSQL instance on Render serves as the data warehouse, accessible directly by Power BI.
- **Optimized Data Model:** A normalized schema with strategic indexing to ensure fast query performance for Power BI dashboards.
- **Standardized DAX Library:** A central set of documented DAX measures ensures metric consistency across all reports.

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Database:** PostgreSQL
- **BI & Visualization:** Power BI (DAX, Power Query M)
- **Cloud & Deployment:** Render (Web Service, PostgreSQL, Cron Jobs)
- **Primary Data Source:** noCRM.io API & Webhooks

## System Architecture

The data flows from the noCRM.io API to Power BI through a cloud-hosted pipeline on Render.

```text
+----------------+      +-------------------------+      +--------------------+      +------------------+
| noCRM.io API   |----->| Daily Python ETL Script |----->|                    |      |                  |
+----------------+      +-------------------------+      |  PostgreSQL DB     |----->|  Power BI        |
                                                         |  (on Render)       |      |  (DirectQuery)   |
+----------------+      +-------------------------+      |                    |      |                  |
| noCRM.io Webhook|----->| Flask Webhook Service   |----->|                    |      |                  |
+----------------+      +-------------------------+      +--------------------+      +------------------+
```



---
### Database and Reporting Structure

The data from these webhooks feeds a structured reporting system in Power BI. The ecosystem is designed as follows:

* **Database Tables**: Each office has three primary tables that are populated by the webhooks. Each table includes a `raw_data` column of type `jsonb` to store the complete, unaltered JSON payload from the webhook for full traceability and future analysis.

    * `lead_created`: This table logs an entry whenever a new lead is created for the first time.
      *Table Structure:*
      | Column Name        | Data Type |
      | ------------------ | --------- |
      | id                 | int8      |
      | event              | text      |
      | signature          | text      |
      | has_succeeded      | bool      |
      | try_count          | int4      |
      | last_returned_code | int4      |
      | received_at        | timestamp |
      | lead_id            | int8      |
      | title              | text      |
      | status             | text      |
      | step               | text      |
      | amount             | numeric   |
      | created_at_utc     | timestamp |
      | updated_at_utc     | timestamp |
      | user_email         | text      |
      | permalink          | text      |
      | raw_data           | jsonb     |
      | client_folder_id   | int8      |
      | client_folder_name | text      |

    * `step_changed`: A new row is added to this table every time an action or status change is applied to an existing lead, creating a complete event history.
      *Table Structure:*
      | Column Name        | Data Type   |
      | ------------------ | ----------- |
      | id                 | int8        |
      | event              | text        |
      | signature          | text        |
      | has_succeeded      | bool        |
      | try_count          | int4        |
      | last_returned_code | int4        |
      | received_at        | timestamptz |
      | lead_id            | int8        |
      | lead_title         | text        |
      | lead_status        | text        |
      | lead_step          | text        |
      | lead_amount        | numeric     |
      | lead_created_at    | timestamptz |
      | lead_updated_at    | timestamptz |
      | lead_user_email    | text        |
      | lead_permalink     | text        |
      | raw_data           | jsonb       |
      | step_id            | int4        |
      | pipeline           | text        |
      | created_at_utc     | timestamptz |
      | updated_at_utc     | timestamptz |
      | moved_by           | text        |

    * `client_folder_created`: This table tracks the creation of new folders, which typically represent a new real estate agent who will manage a portfolio of leads.
      *Table Structure:*
      | Column Name        | Data Type |
      | ------------------ | --------- |
      | id                 | int8      |
      | event              | text      |
      | signature          | text      |
      | has_succeeded      | bool      |
      | try_count          | int4      |
      | last_returned_code | int4      |
      | received_at        | timestamp |
      | folder_id          | int8      |
      | folder_name        | text      |
      | created_at_utc     | timestamp |
      | raw_data           | jsonb     |


* **Power BI Reports**: The real-time data from these tables is surfaced in Power BI through two distinct reports for each office:
    * **Agent Report**: Provides individual sellers with a detailed view of their personal KPIs and lead portfolio.
    * **Manager Report**: Offers a broader set of KPIs for the entire office, including both individual agent performance and overall team metrics.


### 1. ETL & API Synchronization

The ETL process is responsible for both the initial historical data load and the ongoing daily synchronization of new data.

#### **Initial Historical Backfill Strategy**
A significant challenge at the project's outset was retrieving the complete history of all leads and their associated actions dating back to **2018**. The noCRM.io API had a hard limit of **2,000 requests per day**, and with each lead potentially having hundreds of individual actions, a purely API-based backfill was mathematically impossible.

To overcome this, a **hybrid strategy** was implemented:
1.  **Initial Lead Ingestion:** A Python script (shown below) was used to paginate through the API and download the core data for every lead from all three company offices. This captured the primary lead details and the *last known action* for each and insert it in a local database.
2.  **Full Action History Load:** We then requested a complete, one-time database export (as a file) directly from the noCRM.io support team. This file contained the full action history for every lead.
3.  **Manual Data Ingestion:** Using the command-line interface for PostgreSQL, this historical action data was manually uploaded and inserted into the `action_history` table in the **Render** database.

This approach successfully recreated the entire lead history by merging the manually uploaded data with the live data being captured by the webhooks, creating a complete and accurate historical record.

### Ongoing Data Synchronization via Webhooks

After the initial historical backfill, all ongoing data updates are handled in **real-time using webhooks** configured between noCRM and the Flask API hosted on Render. This approach bypasses the need for daily API calls, ensuring that any change in the CRM is reflected in the PostgreSQL database within seconds.

Four key webhooks are configured for each of the three company offices, which trigger on specific CRM events. Each webhook populates a corresponding table in the database to log the event and store its full JSON payload for traceability.

This is an example of how the script to get the Initial Lead Ingestion using the API looks:

```python
import requests
import sqlite3
import time
from datetime import datetime
import pytz

# API and DB Configuration
API_KEY = 'YOUR_NOCRM_API_KEY'
URL = '[https://fiinbro.nocrm.io/api/v2/leads](https://fiinbro.nocrm.io/api/v2/leads)'
DB_FILE = r'C:\sqlite\fiinbro_nocrm.db'
HEADERS = {
    'X-API-KEY': API_KEY,
    'Accept': 'application/json'
}
LIMIT = 100

# Timezone handling for accurate conversion
crm_timezone = pytz.timezone('America/Chihuahua')

def convert_to_crm_timezone(utc_datetime_str):
    if not utc_datetime_str:
        return None
    try:
        # Assumes format "YYYY-MM-DDTHH:MM:SS.sssZ"
        utc_dt = datetime.strptime(utc_datetime_str, "%Y-m-%dT%H:%M:%S.%fZ")
        utc_dt = utc_dt.replace(tzinfo=pytz.utc)
        crm_dt = utc_dt.astimezone(crm_timezone)
        return crm_dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return utc_datetime_str # Fallback for other formats

# Date range for full historical pull
start_date = '2018-01-01T00:00:00.000Z'
end_date = '2025-12-31T23:59:59.999Z'

offset = 0
all_leads = []

# Loop to paginate through all leads from the API
while True:
    params = {'limit': LIMIT, 'offset': offset, 'start_date': start_date, 'end_date': end_date}
    response = requests.get(URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"API Error: {response.status_code} {response.text}")
        break

    leads = response.json()
    if not leads:
        break # Exit loop when no more leads are returned

    all_leads.extend(leads)
    offset += LIMIT
    time.sleep(0.2) # Polite pause to respect API limits

# Connect to SQLite and insert data
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

for lead in all_leads:
    # Prepare data tuple for insertion
    data = (
        lead.get("id"),
        lead.get("title"),
        lead.get("status"),
        lead.get("amount"),
        convert_to_crm_timezone(lead.get("created_at")),
        convert_to_crm_timezone(lead.get("updated_at")),
        convert_to_crm_timezone(lead.get("closed_at")),
        lead.get("user_id"),
        # ... other fields extracted here
    )
    # Use INSERT OR REPLACE to handle duplicates during re-runs
    cur.execute('''
        INSERT OR REPLACE INTO leads (
            id, title, status, amount, created_at, updated_at, closed_at, user_id, ...
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ...)
    ''', data)

conn.commit()
conn.close()
print(f"Database updated with {len(all_leads)} total leads.")
