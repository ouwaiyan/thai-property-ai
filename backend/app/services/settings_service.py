"""Admin settings service — CRUD for ApiSetting rows (API keys, configs)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_setting import ApiSetting


def mask_value(value: str | None) -> str | None:
    """Return a masked representation of a sensitive value."""
    if not value:
        return None
    if len(value) <= 7:
        return "***"
    return value[:3] + "****" + value[-4:]


async def list_all_settings(db: AsyncSession) -> dict[str, list[dict]]:
    """Return all ApiSettings grouped by provider, with values masked."""
    result = await db.execute(
        select(ApiSetting).order_by(ApiSetting.provider, ApiSetting.key_name)
    )
    rows = result.scalars().all()

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        provider = row.provider or "other"
        item = {
            "id": str(row.id),
            "provider": provider,
            "key_name": row.key_name,
            "value": mask_value(row.encrypted_value),
            "has_value": bool(row.encrypted_value),
            "config_json": row.config_json,
            "is_active": row.is_active,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        grouped.setdefault(provider, []).append(item)

    return grouped


async def upsert_setting(
    db: AsyncSession,
    provider: str,
    key_name: str,
    value: str | None = None,
    config_json: dict | None = None,
    is_active: bool | None = None,
) -> dict:
    """Create or update an ApiSetting row. Returns masked representation."""
    result = await db.execute(
        select(ApiSetting).where(
            ApiSetting.provider == provider,
            ApiSetting.key_name == key_name,
        )
    )
    setting = result.scalar_one_or_none()

    if setting:
        if value is not None:
            setting.encrypted_value = value if value != "" else None
        if config_json is not None:
            setting.config_json = config_json
        if is_active is not None:
            setting.is_active = is_active
    else:
        setting = ApiSetting(
            provider=provider,
            key_name=key_name,
            encrypted_value=value if value else None,
            config_json=config_json,
            is_active=True if is_active is None else is_active,
        )
        db.add(setting)

    await db.flush()

    return {
        "id": str(setting.id),
        "provider": setting.provider or provider,
        "key_name": setting.key_name,
        "value": mask_value(setting.encrypted_value),
        "has_value": bool(setting.encrypted_value),
        "config_json": setting.config_json,
        "is_active": setting.is_active,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
    }


async def toggle_setting(db: AsyncSession, setting_id: str, is_active: bool) -> dict | None:
    """Toggle is_active on a single setting. Returns masked representation or None."""
    from uuid import UUID

    result = await db.execute(
        select(ApiSetting).where(ApiSetting.id == UUID(setting_id))
    )
    setting = result.scalar_one_or_none()
    if not setting:
        return None

    setting.is_active = is_active
    await db.flush()

    return {
        "id": str(setting.id),
        "provider": setting.provider,
        "key_name": setting.key_name,
        "value": mask_value(setting.encrypted_value),
        "has_value": bool(setting.encrypted_value),
        "config_json": setting.config_json,
        "is_active": setting.is_active,
        "updated_at": setting.updated_at.isoformat() if setting.updated_at else None,
    }


async def delete_setting(db: AsyncSession, setting_id: str) -> bool:
    """Delete an API setting by id. Returns True if deleted."""
    from uuid import UUID

    result = await db.execute(
        select(ApiSetting).where(ApiSetting.id == UUID(setting_id))
    )
    setting = result.scalar_one_or_none()
    if not setting:
        return False

    await db.delete(setting)
    await db.flush()
    return True


async def test_connection(db: AsyncSession, provider: str) -> dict:
    """Test API connectivity for a provider. Returns {success, message} without leaking keys."""
    if provider == "openai":
        return await _test_openai(db)
    elif provider == "google_maps":
        return await _test_google_maps(db)
    elif provider == "line":
        return await _test_line(db)
    else:
        return {"success": False, "message": f"Unknown provider: {provider}"}


async def _test_openai(db: AsyncSession) -> dict:
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        return {"success": False, "message": "OPENAI_API_KEY 未配置"}
    try:
        from app.utils.ai_client import get_openai_client
        client = get_openai_client()
        resp = await client.models.list()
        model_count = len(resp.data) if resp.data else 0
        return {"success": True, "message": f"连接成功，可用模型数: {model_count}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}


async def _test_google_maps(db: AsyncSession) -> dict:
    from app.config import settings
    if not settings.GOOGLE_MAPS_API_KEY:
        return {"success": False, "message": "GOOGLE_MAPS_API_KEY 未配置"}
    try:
        import httpx
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": "Bangkok", "key": settings.GOOGLE_MAPS_API_KEY}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
        if data.get("status") == "OK":
            return {"success": True, "message": "连接成功，Geocoding API 可用"}
        return {"success": False, "message": f"API 返回异常状态: {data.get('status')}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}


async def _test_line(db: AsyncSession) -> dict:
    from app.config import settings
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return {"success": False, "message": "LINE_CHANNEL_ACCESS_TOKEN 未配置"}
    try:
        import httpx
        url = "https://api.line.me/v2/bot/info"
        headers = {"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get("displayName", "未知")
            return {"success": True, "message": f"连接成功，Bot: {name}"}
        return {"success": False, "message": f"LINE API 返回状态码: {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
