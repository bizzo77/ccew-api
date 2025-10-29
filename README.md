# CCEW API - Proform Electrical

This is the CCEW (Certificate of Compliance for Electrical Work) form generation and submission system.

## Features

- Generates pre-filled CCEW forms from SimPro job data
- Web interface for technicians to complete remaining fields
- Automatic email submission to energy suppliers
- Automatic PDF attachment to SimPro jobs

## Deployment

This app is designed to run on Render.com.

### Environment Variables Required

- `SIMPRO_API_URL`: Your SimPro API base URL
- `SIMPRO_API_KEY`: Your SimPro API bearer token
- `SMTP_SERVER`: Email server for sending CCEWs
- `SMTP_PORT`: Email server port
- `SMTP_USERNAME`: Email username
- `SMTP_PASSWORD`: Email password

## API Endpoints

- `POST /api/ccew/generate` - Generate a new CCEW form session
- `GET /api/ccew/form/<session_id>` - Retrieve form data
- `POST /api/ccew/submit` - Submit completed CCEW

## Tech Stack

- Flask (Python web framework)
- ReportLab (PDF generation)
- SQLite (session storage)
- Vue.js frontend (pre-built in /src/static)

