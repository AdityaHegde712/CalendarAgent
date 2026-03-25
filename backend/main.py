from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from calendar_tools import get_auth_url, complete_auth, _token_file_is_valid

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage

from agent import get_agent

app = FastAPI(title="Calendar Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: session_id -> list of messages
sessions: dict[str, list] = {}


class MessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class MessageResponse(BaseModel):
    session_id: str
    reply: str
    done: bool = True


class AuthStatus(BaseModel):
    authenticated: bool


class AuthUrl(BaseModel):
    url: str


class AuthComplete(BaseModel):
    code: str


def serialize_message(msg: BaseMessage) -> dict:
    return {
        "type": msg.__class__.__name__,
        "content": msg.content if isinstance(msg.content, str) else str(msg.content),
    }


def extract_text_reply(messages: list) -> str:
    """Extract the last AI text reply from the message list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and isinstance(msg.content, str) and msg.content.strip():
            return msg.content.strip()
        if isinstance(msg, AIMessage) and isinstance(msg.content, list):
            text_parts = [p["text"] for p in msg.content if isinstance(p, dict) and p.get("type") == "text"]
            if text_parts:
                return " ".join(text_parts).strip()
    return "I processed your request but have no text reply."


@app.post("/chat", response_model=MessageResponse)
async def chat(req: MessageRequest):
    try:
        session_id = req.session_id or str(uuid.uuid4())

        # Retrieve or init conversation history
        history = sessions.get(session_id, [])

        # Append user message
        history.append(HumanMessage(content=req.message))

        # Run agent
        agent = get_agent()
        result = agent.invoke({"messages": history})

        # Update session with full message history from agent
        sessions[session_id] = list(result["messages"])

        reply = extract_text_reply(result["messages"])

        return MessageResponse(session_id=session_id, reply=reply)

    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@app.get("/auth/status", response_model=AuthStatus)
async def auth_status():
    return AuthStatus(authenticated=_token_file_is_valid())


@app.get("/auth/url", response_model=AuthUrl)
async def auth_url():
    url = get_auth_url()
    if url is None:
        raise HTTPException(status_code=400, detail="Already authenticated")
    return AuthUrl(url=url)


@app.post("/auth/complete")
async def auth_complete(auth: AuthComplete):
    try:
        complete_auth(auth.code)
        return {"status": "authenticated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"status": "cleared"}


@app.get("/health")
async def health():
    return {"status": "ok"}
