# Nistula Technical Assessment

The project is divided into three parts:

1. **Part 1:** Guest Message Handler using FastAPI and Claude API  
2. **Part 2:** PostgreSQL database schema for the unified messaging platform  
3. **Part 3:** Written thinking response for a real guest complaint scenario  

---

## Project Overview

Nistula receives guest messages from multiple channels such as WhatsApp, Booking.com, Airbnb, Instagram and direct enquiries.

This project builds a backend system that:

- Receives inbound guest messages through a webhook endpoint
- Normalises messages into a unified internal schema
- Classifies the message into a query type
- Sends the message to Claude with relevant property context
- Returns a drafted guest reply
- Calculates a confidence score
- Decides whether the reply can be auto-sent, reviewed by an agent or escalated

---

## Repository Structure

```text
nistula-technical-assessment/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── classifier.py
│   ├── claude_client.py
│   ├── confidence.py
│   └── property_context.py
│
├── schema.sql
├── thinking.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Anthropic Claude API
- PostgreSQL

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/fai05/nistula-technical-assessment.git
cd nistula-technical-assessment
```

### 2. Create a virtual environment

For Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not been generated, install manually:

```bash
pip install fastapi uvicorn anthropic python-dotenv pydantic
```

### 4. Create `.env`

Create a `.env` file in the root folder:

```env
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514
```

The actual `.env` file is not included in this repository.

---

## Running the Project

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

If port 8000 is already in use:

```bash
uvicorn app.main:app --reload --port 8001
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

or:

```text
http://127.0.0.1:8001/docs
```

---

## Confidence Scoring Logic

The confidence score is calculated by the backend after Claude generates the drafted reply.

Claude is responsible only for drafting the guest-facing message. The backend calculates the confidence score using deterministic rules so that the logic is transparent and explainable.

The confidence score considers:

- Query type risk
- Whether Claude successfully returned a reply
- Whether the property ID is present
- Whether the booking reference is present
- Message length and clarity
- Number of matching intent keywords
- Whether the message contains mixed intents
- Uncertainty terms such as “maybe”, “not sure” or “if possible”
- High-risk terms such as “refund”, “broken”, “unsafe” or “emergency”
- Whether the message is a complaint

Different query types start with different base confidence scores. For example, check-in and availability questions are usually easier to answer from the property context, while special requests and general enquiries may require agent review.

Complaints are always escalated even if Claude successfully drafts a reply because guest dissatisfaction should be reviewed by a human.

---

## Error Handling

The backend handles errors in the following ways:

- Invalid request payloads return FastAPI validation errors.
- Invalid source values return a `422 Validation Error`.
- Claude API errors return a safe fallback guest reply.
- Confidence score is reduced if Claude does not respond successfully.
- Complaints are always escalated for human review.

---
