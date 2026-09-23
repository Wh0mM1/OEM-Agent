import uuid
import json
import time
import asyncio
from collections import deque
from pathlib import Path
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from core.schemas import ChatRequest, ChatResponse
from agent.graph import automotive_graph
from zoho.mock_client import mock_zoho_client
from zoho.service import zoho_service
from zoho.token_manager import token_manager
from core.config import settings

app = FastAPI(title="Mahindra OEM Conversational AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIST_DIR = BASE_DIR / "static_dist"
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"

# Mount React static assets if built
for dist_dir in [STATIC_DIST_DIR, FRONTEND_DIST_DIR]:
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        break

FALLBACK_ERROR_MESSAGE = (
    "Sorry, I encountered an issue while processing your request. "
    "Please try again or rephrase your question."
)


class RateLimiter:
    """Sliding-window hourly rate limiter for shared OpenRouter key."""
    def __init__(self, max_requests: int = 30, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: deque = deque()

    def _clean_old(self, now: float):
        cutoff = now - self.window_seconds
        while self.timestamps and self.timestamps[0] < cutoff:
            self.timestamps.popleft()

    def check_and_record(self, has_custom_key: bool) -> tuple[bool, int, int]:
        """Returns (is_allowed, current_used_count, remaining_quota)."""
        if has_custom_key:
            return True, len(self.timestamps), 999999

        now = time.time()
        self._clean_old(now)

        if len(self.timestamps) >= self.max_requests:
            return False, len(self.timestamps), 0

        self.timestamps.append(now)
        return True, len(self.timestamps), self.max_requests - len(self.timestamps)

    def get_status(self) -> dict:
        now = time.time()
        self._clean_old(now)
        used = len(self.timestamps)
        return {
            "used_last_hour": used,
            "max_per_hour": self.max_requests,
            "remaining": max(0, self.max_requests - used),
        }


rate_limiter = RateLimiter(max_requests=30, window_seconds=3600)


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    for dist_dir in [STATIC_DIST_DIR, FRONTEND_DIST_DIR]:
        react_index = dist_dir / "index.html"
        if react_index.exists():
            return HTMLResponse(react_index.read_text(encoding="utf-8"))
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Mahindra Automotive AI Agent API is running.</h1>")
    return HTMLResponse(index_file.read_text(encoding="utf-8"))


@app.get("/api/rate-limit/status")
async def get_rate_limit_status():
    """Inspect current shared hourly quota usage."""
    return rate_limiter.get_status()


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Standard REST endpoint with rate limiting & BYOK support."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    thread_id = request.thread_id or session_id

    has_custom_key = bool(request.openrouter_key and request.openrouter_key.strip())
    allowed, used_count, remaining = rate_limiter.check_and_record(has_custom_key)

    if not allowed:
        return ChatResponse(
            session_id=session_id,
            thread_id=thread_id,
            active_stage="quota_exceeded",
            response=(
                "The shared community quota (30 requests/hour) has been reached. "
                "Please provide your own OpenRouter API key and preferred model to continue."
            ),
            tool_chips=[{
                "tool_name": "rate_limiter",
                "status": "error",
                "label": "Hourly Quota Reached (30/30 req)",
                "data": {"used": used_count, "limit": 30},
            }],
            collected_slots={},
            crm_ids={},
            requires_custom_key=True,
            rate_limit_info=rate_limiter.get_status(),
        )

    config = {"configurable": {"thread_id": thread_id}}
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "session_id": session_id,
        "thread_id": thread_id,
        "custom_llm_key": request.openrouter_key.strip() if request.openrouter_key else None,
        "custom_llm_model": request.openrouter_model.strip() if request.openrouter_model else None,
    }

    try:
        final_state = await automotive_graph.ainvoke(inputs, config=config)
        messages = final_state.get("messages", [])
        last_message = messages[-1].content if messages else FALLBACK_ERROR_MESSAGE

        return ChatResponse(
            session_id=session_id,
            thread_id=thread_id,
            active_stage=final_state.get("active_stage", "new_lead"),
            response=str(last_message),
            tool_chips=final_state.get("tool_chips", []),
            collected_slots=final_state.get("collected_slots", {}),
            crm_ids=final_state.get("crm_ids", {}),
            requires_custom_key=False,
            rate_limit_info=rate_limiter.get_status(),
        )
    except Exception as e:
        # Graceful fallback: Never crash or dump raw stack traces
        return ChatResponse(
            session_id=session_id,
            thread_id=thread_id,
            active_stage="ambiguous",
            response=FALLBACK_ERROR_MESSAGE,
            tool_chips=[{
                "tool_name": "error_handler",
                "status": "error",
                "label": "Auto-recovery: Please try again",
                "data": {"error": str(e)},
            }],
            collected_slots={},
            crm_ids={},
            requires_custom_key=False,
            rate_limit_info=rate_limiter.get_status(),
        )


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Server-Sent Events (SSE) streaming endpoint with rate limiting & BYOK support."""
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    thread_id = request.thread_id or session_id

    has_custom_key = bool(request.openrouter_key and request.openrouter_key.strip())
    allowed, used_count, remaining = rate_limiter.check_and_record(has_custom_key)

    if not allowed:
        async def quota_event_generator() -> AsyncGenerator[str, None]:
            msg = (
                "The shared community quota (30 requests/hour) has been reached. "
                "Please provide your own OpenRouter API key and preferred model to continue."
            )
            yield f"data: {json.dumps({'type': 'init', 'session_id': session_id, 'thread_id': thread_id})}\n\n"
            yield f"data: {json.dumps({'type': 'meta', 'stage': 'quota_exceeded', 'tool_chips': [{'tool_name': 'rate_limiter', 'status': 'error', 'label': 'Hourly Quota Reached (30/30 req)'}], 'requires_custom_key': True, 'rate_limit_info': rate_limiter.get_status()})}\n\n"
            yield f"data: {json.dumps({'type': 'chunk', 'text': msg})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(
            quota_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "session_id": session_id,
            "thread_id": thread_id,
            "custom_llm_key": request.openrouter_key.strip() if request.openrouter_key else None,
            "custom_llm_model": request.openrouter_model.strip() if request.openrouter_model else None,
        }

        try:
            # Yield initial acknowledgement event
            yield f"data: {json.dumps({'type': 'init', 'session_id': session_id, 'thread_id': thread_id})}\n\n"

            # Execute graph and retrieve state
            final_state = await automotive_graph.ainvoke(inputs, config=config)
            messages = final_state.get("messages", [])
            full_text = str(messages[-1].content) if messages else FALLBACK_ERROR_MESSAGE

            # Stream metadata and tool chips first
            yield f"data: {json.dumps({'type': 'meta', 'stage': final_state.get('active_stage', 'new_lead'), 'tool_chips': final_state.get('tool_chips', []), 'requires_custom_key': False, 'rate_limit_info': rate_limiter.get_status()})}\n\n"

            # Stream text chunks progressively to simulate smooth token streaming
            words = full_text.split(" ")
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size]) + " "
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk})}\n\n"
                await asyncio.sleep(0.02)  # 20ms pacing for smooth rendering

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Catch-all graceful fallback for streaming
            yield f"data: {json.dumps({'type': 'error', 'text': FALLBACK_ERROR_MESSAGE})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/crm/status")
async def get_crm_status():
    """Inspects live or mock CRM records for the UI verification drawer."""
    if zoho_service.is_live:
        try:
            # Fetch real live records from Zoho CRM
            leads_res = await token_manager.execute_with_token(
                "GET", "Leads", params={"fields": "id,Full_Name,Phone,Email,City,Vehicle_Model_of_Interest,Lead_Source"}
            )
            deals_res = await token_manager.execute_with_token(
                "GET", "Deals", params={"fields": "id,Deal_Name,Stage,Amount,Description,Closing_Date,VIN"}
            )
            cases_res = await token_manager.execute_with_token(
                "GET", "Cases", params={"fields": "id,Case_Number,Subject,Status,Priority,Preferred_Center,Deal_Name,Related_To"}
            )
            return {
                "mode": "live",
                "dc": settings.ZOHO_DC,
                "records": {
                    "leads": leads_res.get("data", []),
                    "deals": deals_res.get("data", []),
                    "cases": cases_res.get("data", []),
                },
            }
        except Exception as e:
            print(f"Error fetching live CRM status: {e}")

    # Fallback to mock records if offline
    return {
        "mode": "mock",
        "dc": settings.ZOHO_DC,
        "records": mock_zoho_client.inspect_database(),
    }


@app.post("/api/session/reset")
async def reset_session():
    return {"message": "Session reset successful."}
