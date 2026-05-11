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
|
├── app/
│   ├── main.py
│   ├── models.py
│   ├── classifier.py
│   ├── claude_client.py
│   ├── confidence.py
│   └── property_context.py
|
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

The endpoint returns `confidence_score` as a number between `0` and `1`. Claude is responsible only for drafting the guest-facing message. The backend calculates the confidence score using deterministic rules so the logic is transparent, explainable, and does not simply return `1.0` whenever a reply is generated.

Scoring starts from the classified query type:

| Query type | Base score | Reason |
| --- | ---: | --- |
| `post_sales_checkin` | `0.76` | Usually answerable from property context. |
| `pre_sales_availability` | `0.74` | Usually answerable when dates/property are clear. |
| `pre_sales_pricing` | `0.72` | Answerable, but pricing can need review if complex. |
| `special_request` | `0.63` | Often needs operational confirmation. |
| `general_enquiry` | `0.58` | Intent is less specific. |
| `complaint` | `0.45` | Always needs human escalation. |

The score is then adjusted using these signals:

- `+0.08` if Claude successfully drafts a reply, `-0.30` if the fallback reply is used.
- `+0.04` when `property_id` is present, `-0.08` when missing.
- Booking-related messages (`post_sales_checkin`, `special_request`, `complaint`) get `+0.04` when `booking_ref` is present and `-0.04` when missing.
- Very short messages lose confidence because they are harder to interpret.
- Messages with keywords matching the classified query type gain confidence.
- Messages with multiple intent groups, uncertainty terms, several questions, or high-risk wording lose confidence.
- Complaints are capped at `0.55`.
- Non-complaint messages are capped at `0.95`, so the service avoids overconfident `1.0` scores.

Complaints are always escalated even if Claude successfully drafts a reply because guest dissatisfaction should be reviewed by a human.

---

## Action Logic

The `action` field is derived from the score:

| Condition | Action |
| --- | --- |
| Complaint | `escalate` |
| `confidence_score > 0.85` | `auto_send` |
| `0.60 <= confidence_score <= 0.85` | `agent_review` |
| `confidence_score < 0.60` | `escalate` |

Example response:

```json
{
  "message_id": "uuid",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul, great news...",
  "confidence_score": 0.91,
  "action": "auto_send"
}
```

---

## Error Handling

The backend handles errors in the following ways:

- Invalid request payloads return FastAPI validation errors.
- Invalid source values return a `422 Validation Error`.
- Claude API errors return a safe fallback guest reply.
- Confidence score is reduced if Claude does not respond successfully.
- Complaints are always escalated for human review.

