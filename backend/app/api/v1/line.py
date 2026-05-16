"""LINE Messaging API endpoints — webhook, conversations, reply."""
from math import ceil
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_data_entry
from app.dependencies import get_db
from app.models.user import User
from app.schemas.line import (
    LineAIReplyResponse,
    LineConversationOut,
    LinePushRequest,
    LineReplyRequest,
)
from app.services.line_service import (
    generate_ai_reply_suggestion,
    get_line_conversation,
    list_line_conversations,
    process_webhook_event,
    push_line_message,
    reply_line_message,
    verify_signature,
)

router = APIRouter(prefix="/line", tags=["LINE"])


@router.post("/webhook")
async def line_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """LINE webhook endpoint. Public — uses HMAC-SHA256 signature verification."""
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="line.invalid_signature")

    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="line.invalid_json")

    events = data.get("events", [])
    results = []
    for event in events:
        try:
            result = await process_webhook_event(db, event)
            if result:
                results.append(result)
        except Exception:
            pass

    return {"status": "ok", "processed": len(results)}


@router.get("/conversations")
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List LINE conversations with pagination."""
    items, total = await list_line_conversations(db, page, page_size, status)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/conversations/{line_user_id}", response_model=LineConversationOut)
async def get_conversation(
    line_user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation detail for a LINE user."""
    conv = await get_line_conversation(db, line_user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="line.conversation_not_found")
    return LineConversationOut(**conv)


@router.post("/conversations/{line_user_id}/ai-reply", response_model=LineAIReplyResponse)
async def suggest_ai_reply(
    line_user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Generate AI reply suggestion for the latest incoming message in a conversation."""
    conv = await get_line_conversation(db, line_user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="line.conversation_not_found")

    # Find the latest incoming message
    incoming = None
    for msg in reversed(conv["messages"]):
        if msg.direction == "incoming":
            incoming = msg
            break

    if not incoming:
        raise HTTPException(status_code=400, detail="line.no_incoming_message")

    if not conv.get("lead_id"):
        raise HTTPException(status_code=400, detail="line.no_lead_associated")

    suggested = await generate_ai_reply_suggestion(
        db, UUID(conv["lead_id"]), incoming.message_text
    )

    return LineAIReplyResponse(
        suggested_reply=suggested or "(AI reply generation failed)",
        lead_context={
            "lead_id": conv["lead_id"],
            "lead_name": conv.get("lead_name"),
        },
    )


@router.post("/push", status_code=200)
async def push_message(
    body: LinePushRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Push a message to a LINE user. Records outgoing message and updates lead status."""
    result = await push_line_message(db, body.line_user_id, body.message_text, user_id=current_user.id)
    if not result["success"]:
        raise HTTPException(status_code=502, detail=result.get("error") or "line.push_failed")
    return {"status": "sent", "message_id": result.get("message_id")}


@router.post("/reply", status_code=200)
async def reply_message(
    body: LineReplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_data_entry),
):
    """Reply to a LINE message. Records outgoing message and updates lead status."""
    result = await reply_line_message(
        db, body.reply_token, body.message_text,
        line_user_id=body.line_user_id or "", user_id=current_user.id,
    )
    if not result["success"]:
        raise HTTPException(status_code=502, detail=result.get("error") or "line.reply_failed")
    return {"status": "sent", "message_id": result.get("message_id")}
