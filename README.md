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
