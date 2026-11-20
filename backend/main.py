
import os
import hmac
import hashlib
import secrets
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import (
    initialize_database,
    create_conversation,
    save_message,
    get_history,
    clear_conversation,
    list_faqs,
    insert_faq
)

from .seed import seed_faqs

from .ai_service import (
    retrieve_faqs,
    generate_answer,
    NOT_FOUND_MESSAGE,
    AI_UNAVAILABLE_MESSAGE
)


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="AskSE API",
    version="1.0.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)


# ==========================================
# 2. ADMIN CONFIGURATION
# ==========================================

ADMIN_PIN = os.getenv("ADMIN_PIN", "2026")

ADMIN_SECRET = os.getenv(
    "ADMIN_SECRET",
    "change-this-secret-before-deployment"
)


# ==========================================
# 3. REQUEST MODELS
# ==========================================

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=300)
    language: str = Field(default="English")
    conversation_id: Optional[int] = None


class LoginRequest(BaseModel):
    pin: str = Field(min_length=1, max_length=20)


class FAQCreateRequest(BaseModel):
    question: str = Field(min_length=3, max_length=300)
    answer: str = Field(min_length=3, max_length=3000)
    category: str = Field(
        default="General",
        min_length=1,
        max_length=80
    )


# ==========================================
# 4. ADMIN AUTHENTICATION
# ==========================================

def make_admin_token():

    nonce = secrets.token_urlsafe(24)

    signature = hmac.new(
        ADMIN_SECRET.encode(),
        nonce.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{nonce}.{signature}"


def verify_admin_token(token):

    if not token or "." not in token:
        return False

    nonce, signature = token.rsplit(".", 1)

    expected = hmac.new(
        ADMIN_SECRET.encode(),
        nonce.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def require_admin(authorization):

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Admin login required"
        )

    token = authorization.split(" ", 1)[1]

    if not verify_admin_token(token):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired admin session"
        )


# ==========================================
# 5. DATABASE STARTUP
# ==========================================

@app.on_event("startup")
def startup():

    initialize_database()

    seed_faqs()

    print("AskSE database initialized successfully.")


# ==========================================
# 6. HOME PAGE
# ==========================================

@app.get("/")
def home():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ==========================================
# 7. HEALTH CHECK
# ==========================================

@app.get("/api/health")
def health():

    return {
        "status": "ok",
        "application": "AskSE"
    }


# ==========================================
# 8. GET FAQs
# ==========================================

@app.get("/api/faqs")
def faqs():

    return {
        "faqs": list_faqs(active_only=True)
    }


# ==========================================
# 9. ADMIN LOGIN
# ==========================================

@app.post("/api/admin/login")
def admin_login(payload: LoginRequest):

    if not hmac.compare_digest(payload.pin, ADMIN_PIN):
        raise HTTPException(
            status_code=401,
            detail="Incorrect admin PIN"
        )

    return {
        "success": True,
        "token": make_admin_token()
    }


# ==========================================
# 10. ADD NEW FAQ
# ==========================================

@app.post("/api/admin/faqs")
def admin_create_faq(
    payload: FAQCreateRequest,
    authorization: Optional[str] = Header(default=None)
):

    require_admin(authorization)

    try:

        faq_code = insert_faq(
            payload.question,
            payload.answer,
            payload.category
        )

    except Exception as e:

        print("FAQ SAVE ERROR:", repr(e))

        raise HTTPException(
            status_code=400,
            detail="Could not save FAQ. Check for duplicate content."
        )

    return {
        "success": True,
        "faq_code": faq_code
    }


# ==========================================
# 11. CHAT API
# ==========================================

@app.post("/api/chat")
async def chat(payload: ChatRequest):

    question = payload.question.strip()

    if not question:

        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty"
        )

    if len(question) > 300:

        raise HTTPException(
            status_code=422,
            detail="Question must be 300 characters or fewer"
        )

    language = (
        payload.language
        if payload.language in ["English", "Roman Urdu"]
        else "English"
    )

    conversation_id = payload.conversation_id

    # Create or verify conversation.

    if conversation_id is None:

        conversation_id = create_conversation()

    else:

        from .database import get_connection

        with get_connection() as conn:

            exists = conn.execute(
                """
                SELECT conversation_id
                FROM conversations
                WHERE conversation_id = ?
                """,
                (conversation_id,)
            ).fetchone()

        if not exists:

            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )

    # Save the question before AI processing.

    save_message(
        conversation_id,
        "user",
        question,
        language,
        []
    )

    try:

        faqs = list_faqs(active_only=True)

        relevant = retrieve_faqs(
            question,
            faqs
        )

        # If no relevant FAQ is found.

        if not relevant:

            result = {
                "found": False,
                "answer": NOT_FOUND_MESSAGE,
                "faq_ids": []
            }

        else:

            result = await generate_answer(
                question,
                language,
                relevant
            )

        # Save AI response.

        save_message(
            conversation_id,
            "assistant",
            result["answer"],
            language,
            result["faq_ids"]
        )

        return {
            "found": result["found"],
            "answer": result["answer"],
            "faq_ids": result["faq_ids"],
            "conversation_id": conversation_id
        }

    except Exception as e:

        print("AI API ERROR:", repr(e))

        raise HTTPException(
            status_code=503,
            detail=AI_UNAVAILABLE_MESSAGE
        )


# ==========================================
# 12. CHAT HISTORY
# ==========================================

@app.get("/api/history/{conversation_id}")
def history(conversation_id: int):

    from .database import get_connection

    with get_connection() as conn:

        exists = conn.execute(
            """
            SELECT conversation_id
            FROM conversations
            WHERE conversation_id = ?
            """,
            (conversation_id,)
        ).fetchone()

    if not exists:

        return {
            "conversation_id": conversation_id,
            "messages": []
        }

    return {
        "conversation_id": conversation_id,
        "messages": get_history(conversation_id)
    }


# ==========================================
# 13. CLEAR CHAT HISTORY
# ==========================================

@app.delete("/api/history/{conversation_id}")
def delete_history(conversation_id: int):

    clear_conversation(conversation_id)

    return {
        "success": True
    }


# ==========================================
# END OF ASKSE BACKEND
# ==========================================
