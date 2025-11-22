# Project Startup Guide

This guide walks through everything needed to run AgentCoach360 locally and deploy it to Google Cloud Run.

It is intentionally written for developers who clone the repository for the first time.

---

# 1. Clone the Repository

```bash
git clone <your_repo_url>
cd agentcoach360 
```
# 2. Create and Activate a Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
```
# 3. Install Dependencies
```bash
pip install -r requirements.txt
```
# 3. Install Dependencies
```bash
pip install -r requirements.txt
```
Dependencies include:

FastAPI

Uvicorn

ADK (Google)

google-genai

sqlite3 (built-in)

python-dotenv

# 4. Environment Variables
```bash
agentcoach360_backend/.env
```
Add:
```bash
GOOGLE_API_KEY=YOUR_KEY_HERE
```
Cloud Run will inject the same variable during deployment.
# 5. Running the Backend Locally
```bash
uvicorn web_app:app --reload --port 8000
```
This starts:

the FastAPI API,

the entire multi-agent system,

memory,

logs,

and the chat UI.

Visit:
```bash
http://127.0.0.1:8000
```
# 6. Running the Terminal Agent (ADK Runner)
This is optional but useful for debugging.

From project root:
```bash
adk run agentcoach360_backend
```
This runs the root agent in your terminal using the same session service and tools.

# 7. Where Data Is Stored
```bash
/data/memory.sqlite   # long-term memory
/logs/interactions.csv  # observability
```
Safe to delete if you need a fresh start.

# 8. Deployment (Google Cloud Run)
 you can also run to the cloud following the gCloud docs


