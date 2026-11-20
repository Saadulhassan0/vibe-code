# AskSE — AI University Help Desk

## 1. Requirements
- Python 3.10 or newer
- Internet connection for the hosted LLM API
- A hosted LLM API key (default configuration uses Groq's OpenAI-compatible endpoint)

## 2. Open the project
Open this folder in VS Code:
`AskSE`

## 3. Create a virtual environment (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this only for the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

## 5. Configure the AI key
Copy `.env.example` and name the copy `.env`.
Open `.env` and replace `put_your_real_api_key_here` with your actual hosted LLM API key.

Do not put the key in `frontend/script.js`, HTML, GitHub, or screenshots.

## 6. Run AskSE
From the main AskSE folder:
```powershell
python -m uvicorn backend.main:app --reload
```

Open:
http://127.0.0.1:8000

API documentation:
http://127.0.0.1:8000/docs

Health check:
http://127.0.0.1:8000/api/health

## 7. Admin
Click Admin and use the competition PIN:
`2026`

Add an approved FAQ with its question, answer and category. The FAQ becomes available to retrieval immediately.

## 8. Database
SQLite file is created automatically at:
`data/askse.db`

The eight official starter FAQs are seeded once and are not duplicated on restart.

## 9. Important testing
1. Ask: `What are the library timings?`
2. Ask: `What is the attendance requirement?`
3. Ask an unsupported question and verify the exact not-found response.
4. Ask in Roman Urdu.
5. Add a new FAQ in Admin, then ask about it.
6. Refresh the browser and verify chat history.
7. Test Clear Chat and cancel/confirm.
8. Temporarily remove the API key and verify the AI unavailable message and retained question.

## 10. Before public deployment
- Set a strong `ADMIN_SECRET`.
- Configure a strong admin PIN if the competition permits it.
- Never commit `.env`.
- Use HTTPS.
- Restrict admin access and add rate limiting if deploying publicly.
- Review the final competition rubric and test each mandatory criterion.
