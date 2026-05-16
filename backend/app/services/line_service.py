"""LINE Messaging API service — webhook handling, AI replies, push messaging."""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.lead import Lead
from app.models.line_message import LineMessage
from app.services.ai_service import ai_parse_lead_needs


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify LINE webhook HMAC-SHA256 signature."""
    if not settings.LINE_CHANNEL_SECRET:
        return False
    expected = hmac.new(
        settings.LINE_CHANNEL_SECRET.encode(),
        body,
        hashlib.sha256,
    ).digest()
    expected_b64 = __import__("base64").b64encode(expected).decode()
    return hmac.compare_digest(expected_b64, signature)


async def process_webhook_event(
    db: AsyncSession,
    event: dict,
) -> dict | None:
    """Process a single LINE webhook event. Returns a result dict for logging."""
    event_type = event.get("type", "")

    if event_type != "message":
        return None

    message = event.get("message", {})
    if message.get("type") != "text":
        return None

    source = event.get("source", {})
    line_user_id = source.get("userId") or source.get("userId", "")
    if not line_user_id:
        return None

    reply_token = event.get("replyToken", "")
    message_text = message.get("text", "").strip()
    if not message_text:
        return None

    # Find or create lead for this LINE user
    lead = await _find_or_create_line_lead(db, line_user_id)

    # Store incoming message
    incoming = LineMessage(
        line_user_id=line_user_id,
        lead_id=lead.id,
        message_text=message_text,
        direction="incoming",
        message_type="text",
        reply_token=reply_token,
        source_type=source.get("type", "user"),
    )
    db.add(incoming)

    # Mark lead as needing reply
    if lead.status in ("new", "parsed"):
        lead.status = "pending_reply"

    await db.flush()

    # Check auto-reply setting
    auto_reply = await get_auto_reply_setting(db)
    auto_replied = False
    if auto_reply and settings.OPENAI_API_KEY and reply_token:
        try:
            ai_reply = await generate_ai_reply_suggestion(db, lead.id, message_text)
            if ai_reply:
                reply_result = await reply_line_message(db, reply_token, ai_reply, line_user_id)
                auto_replied = reply_result.get("success", False)
        except Exception:
            auto_replied = False

    return {
        "line_user_id": line_user_id,
        "lead_id": str(lead.id),
        "action": "auto_replied" if auto_replied else "stored",
        "lead_status": lead.status,
        "auto_reply_enabled": auto_reply,
    }


async def _find_or_create_line_lead(
    db: AsyncSession, line_user_id: str
) -> Lead:
    """Find existing lead by line_user_id, or create a new one."""
    result = await db.execute(
        select(Lead).where(Lead.line_user_id == line_user_id)
    )
    lead = result.scalar_one_or_none()
    if lead:
        return lead

    lead = Lead(
        name=f"LINE User {line_user_id[:8]}",
        original_message="(LINE conversation started)",
        source="line",
        line_user_id=line_user_id,
        status="new",
    )
    db.add(lead)
    await db.flush()

    # n8n: notify on new LINE lead
    from app.services.n8n_service import trigger_new_lead_notification
    await trigger_new_lead_notification(db, str(lead.id), lead.name)

    return lead


async def generate_ai_reply_suggestion(
    db: AsyncSession,
    lead_id: UUID,
    incoming_message: str,
) -> str | None:
    """Generate an AI-suggested reply for a lead's incoming message. Never auto-sends."""
    if not settings.OPENAI_API_KEY:
        return None

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        return None

    # Get recent conversation for context
    recent = await db.execute(
        select(LineMessage)
        .where(LineMessage.lead_id == lead_id)
        .order_by(LineMessage.created_at.desc())
        .limit(10)
    )
    recent_messages = list(recent.scalars().all())
    recent_messages.reverse()

    history = "\n".join(
        f"{'Customer' if m.direction == 'incoming' else 'Agent'}: {m.message_text[:200]}"
        for m in recent_messages
    )

    lang_map = {"zh": "中文", "en": "English", "th": "Thai"}
    language = lang_map.get(lead.language or "zh", "Chinese")

    from app.utils.ai_client import simple_chat

    system_prompt = (
        f"You are a Thai real estate agent. Reply in {language}. "
        f"Given the conversation history, suggest a helpful, professional reply "
        f"to the customer's latest message. Be concise (2-4 sentences). "
        f"If the customer is asking about properties, ask clarifying questions "
        f"about their budget, preferred location, and bedroom needs."
    )

    user_message = (
        f"Lead name: {lead.name}\n"
        f"Parsed needs: {json.dumps(lead.parsed_needs or {}, ensure_ascii=False)}\n"
        f"Conversation:\n{history}\n"
        f"Latest customer message: {incoming_message}\n\n"
        f"Suggested reply:"
    )

    try:
        reply = await simple_chat(system_prompt, user_message, temperature=0.7)
        return reply
    except Exception:
        return None


async def push_line_message(
    db: AsyncSession,
    line_user_id: str,
    message_text: str,
    user_id: UUID | None = None,
) -> dict:
    """Push a message to a LINE user and record it in the local database.

    Returns dict with keys: success, error, line_user_id, message_id.
    """
    result = {"success": False, "error": None, "line_user_id": line_user_id, "message_id": None}

    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        result["error"] = "line.channel_token_not_configured"
        return result

    # Find lead for this LINE user
    lead_result = await db.execute(
        select(Lead).where(Lead.line_user_id == line_user_id)
    )
    lead = lead_result.scalar_one_or_none()

    # Create outgoing message record
    outgoing = LineMessage(
        line_user_id=line_user_id,
        lead_id=lead.id if lead else None,
        message_text=message_text,
        direction="outgoing",
        message_type="text",
        source_type="agent",
    )
    db.add(outgoing)
    await db.flush()
    result["message_id"] = str(outgoing.id)

    # Send via LINE API
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "to": line_user_id,
        "messages": [{"type": "text", "text": message_text}],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if resp.status_code == 200:
                result["success"] = True
                # Update lead status to contacted
                if lead and lead.status in ("new", "parsed", "pending_reply"):
                    lead.status = "contacted"
                    await db.flush()
            else:
                result["error"] = resp_data.get("message") or f"line.api_error||status={resp.status_code}"
    except Exception as e:
        result["error"] = f"line.api_request_failed||error={str(e)}"

    # Audit log
    if user_id:
        from app.services.audit_service import log
        await log(
            db,
            user_id=user_id,
            action="line_push",
            entity_type="LineMessage",
            entity_id=outgoing.id,
            after_json={"line_user_id": line_user_id, "text_preview": message_text[:100], "success": result["success"]},
        )

    return result


async def reply_line_message(
    db: AsyncSession,
    reply_token: str,
    message_text: str,
    line_user_id: str = "",
    user_id: UUID | None = None,
) -> dict:
    """Reply to a LINE message and record it locally.

    Returns dict with keys: success, error, reply_token, message_id.
    """
    result = {"success": False, "error": None, "reply_token": reply_token, "message_id": None}

    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        result["error"] = "line.channel_token_not_configured"
        return result

    # Find lead for this LINE user
    lead = None
    if line_user_id:
        lead_result = await db.execute(
            select(Lead).where(Lead.line_user_id == line_user_id)
        )
        lead = lead_result.scalar_one_or_none()

    # Create outgoing message record
    outgoing = LineMessage(
        line_user_id=line_user_id or reply_token[:16],
        lead_id=lead.id if lead else None,
        message_text=message_text,
        direction="outgoing",
        message_type="text",
        reply_token=reply_token,
        source_type="agent",
    )
    db.add(outgoing)
    await db.flush()
    result["message_id"] = str(outgoing.id)

    # Send via LINE API
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message_text}],
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            if resp.status_code == 200:
                result["success"] = True
                if lead and lead.status in ("new", "parsed", "pending_reply"):
                    lead.status = "contacted"
                    await db.flush()
            else:
                result["error"] = resp_data.get("message") or f"line.api_error||status={resp.status_code}"
    except Exception as e:
        result["error"] = f"line.api_request_failed||error={str(e)}"

    # Audit log
    if user_id:
        from app.services.audit_service import log
        await log(
            db,
            user_id=user_id,
            action="line_reply",
            entity_type="LineMessage",
            entity_id=outgoing.id,
            after_json={"line_user_id": line_user_id, "reply_token": reply_token, "text_preview": message_text[:100], "success": result["success"]},
        )

    return result


async def get_line_conversation(
    db: AsyncSession,
    line_user_id: str,
) -> dict | None:
    """Get conversation details for a LINE user."""
    lead_result = await db.execute(
        select(Lead).where(Lead.line_user_id == line_user_id)
    )
    lead = lead_result.scalar_one_or_none()

    msg_result = await db.execute(
        select(LineMessage)
        .where(LineMessage.line_user_id == line_user_id)
        .order_by(LineMessage.created_at.asc())
    )
    messages = list(msg_result.scalars().all())

    if not messages:
        return None

    return {
        "line_user_id": line_user_id,
        "lead_id": str(lead.id) if lead else None,
        "lead_name": lead.name if lead else None,
        "messages": messages,
        "latest_message_at": messages[-1].created_at if messages else None,
    }


# ── Rich Menu ────────────────────────────────────────────────────────

def _line_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


async def create_rich_menu(menu_config: dict) -> dict:
    """Create a rich menu on LINE. menu_config matches LINE API spec."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        raise ValueError("line.channel_token_not_configured")

    url = "https://api.line.me/v2/bot/richmenu"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=menu_config, headers=_line_headers())
            data = resp.json()
            if resp.status_code not in (200, 202):
                raise ValueError(data.get("message") or f"line.api_error||status={resp.status_code}")
            return data
    except httpx.HTTPError as e:
        raise ValueError(f"line.api_request_failed||error={str(e)}")


async def set_default_rich_menu(rich_menu_id: str) -> bool:
    """Set a rich menu as the default for all users."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return False
    url = f"https://api.line.me/v2/bot/all/richmenu/{rich_menu_id}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=_line_headers())
            return resp.status_code in (200, 202)
    except Exception:
        return False


async def delete_rich_menu(rich_menu_id: str) -> bool:
    """Delete a rich menu from LINE."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return False
    url = f"https://api.line.me/v2/bot/richmenu/{rich_menu_id}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(url, headers=_line_headers())
            return resp.status_code == 200
    except Exception:
        return False


async def upload_rich_menu_image(rich_menu_id: str, image_bytes: bytes, content_type: str) -> bool:
    """Upload an image for a rich menu. Image must match the menu dimensions."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        raise ValueError("line.channel_token_not_configured")
    url = f"https://api-api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
    headers = {"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                content=image_bytes,
                headers={**headers, "Content-Type": content_type},
            )
            if resp.status_code in (200, 202):
                return True
            raise ValueError(resp.text or f"line.api_error||status={resp.status_code}")
    except httpx.HTTPError as e:
        raise ValueError(f"line.api_request_failed||error={str(e)}")


async def list_rich_menus() -> list[dict]:
    """List all rich menus from LINE."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return []
    url = "https://api.line.me/v2/bot/richmenu/list"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=_line_headers())
            if resp.status_code == 200:
                data = resp.json()
                return data.get("richmenus", [])
            return []
    except Exception:
        return []


async def get_default_rich_menu() -> dict | None:
    """Get the current default rich menu ID."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return None
    url = "https://api.line.me/v2/bot/all/richmenu"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers=_line_headers())
            if resp.status_code == 200:
                data = resp.json()
                return data
            return None
    except Exception:
        return None


async def get_auto_reply_setting(db: AsyncSession) -> bool:
    """Check if auto-reply is enabled in api_settings."""
    from app.models.api_setting import ApiSetting
    result = await db.execute(
        select(ApiSetting).where(
            ApiSetting.provider == "line",
            ApiSetting.key_name == "auto_reply_enabled",
        )
    )
    setting = result.scalar_one_or_none()
    if setting and setting.config_json:
        return setting.config_json.get("enabled", False)
    return False


async def set_auto_reply_setting(db: AsyncSession, enabled: bool, user_id) -> None:
    """Enable or disable auto-reply."""
    from app.models.api_setting import ApiSetting
    result = await db.execute(
        select(ApiSetting).where(
            ApiSetting.provider == "line",
            ApiSetting.key_name == "auto_reply_enabled",
        )
    )
    setting = result.scalar_one_or_none()
    if setting:
        setting.config_json = {"enabled": enabled}
    else:
        setting = ApiSetting(
            provider="line",
            key_name="auto_reply_enabled",
            config_json={"enabled": enabled},
        )
        db.add(setting)
    await db.flush()


async def list_line_conversations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
) -> tuple[list[dict], int]:
    """List LINE conversations (grouped by line_user_id)."""
    subquery = (
        select(
            LineMessage.line_user_id,
            LineMessage.created_at.label("latest_msg_at"),
        )
        .group_by(LineMessage.line_user_id)
        .subquery()
    )

    from sqlalchemy import func

    count_result = await db.execute(
        select(func.count()).select_from(subquery)
    )
    total = count_result.scalar() or 0

    query = (
        select(
            LineMessage.line_user_id,
            Lead.id.label("lead_id"),
            Lead.name.label("lead_name"),
            Lead.status.label("lead_status"),
            func.max(LineMessage.created_at).label("latest_msg_at"),
            func.count(LineMessage.id).label("message_count"),
        )
        .outerjoin(Lead, LineMessage.lead_id == Lead.id)
        .group_by(
            LineMessage.line_user_id,
            Lead.id,
            Lead.name,
            Lead.status,
        )
        .order_by(func.max(LineMessage.created_at).desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if status:
        query = query.where(Lead.status == status)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for row in rows:
        items.append({
            "line_user_id": row.line_user_id,
            "lead_id": str(row.lead_id) if row.lead_id else None,
            "lead_name": row.lead_name or f"LINE User {row.line_user_id[:8]}",
            "lead_status": row.lead_status or "new",
            "latest_message_at": row.latest_msg_at,
            "message_count": row.message_count,
        })

    return items, total
