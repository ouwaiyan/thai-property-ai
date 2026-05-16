"""LINE Rich Menu management and auto-reply settings."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin, require_data_entry
from app.dependencies import get_db
from app.models.user import User
from app.services.line_service import (
    create_rich_menu,
    delete_rich_menu,
    get_auto_reply_setting,
    get_default_rich_menu,
    list_rich_menus,
    set_auto_reply_setting,
    set_default_rich_menu,
)

router = APIRouter(prefix="/line/settings", tags=["LINE Settings"])


class AutoReplyStatus(BaseModel):
    enabled: bool


class AutoReplyToggleRequest(BaseModel):
    enabled: bool


class RichMenuCreateRequest(BaseModel):
    name: str = Field(..., description="Rich menu display name")
    chat_bar_text: str = Field(default="Menu", description="Text shown in chat bar")
    areas: list[dict] = Field(
        default_factory=lambda: [
            {
                "bounds": {"x": 0, "y": 0, "width": 1250, "height": 840},
                "action": {"type": "postback", "data": "action=find_property", "label": "找房"},
            },
            {
                "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 840},
                "action": {"type": "postback", "data": "action=book_viewing", "label": "预约看房"},
            },
            {
                "bounds": {"x": 0, "y": 840, "width": 1250, "height": 840},
                "action": {"type": "message", "text": "发送位置"},
            },
            {
                "bounds": {"x": 1250, "y": 840, "width": 1250, "height": 840},
                "action": {"type": "message", "text": "咨询经纪人"},
            },
        ],
        description="Tap areas with actions",
    )
    size: dict = Field(
        default_factory=lambda: {"width": 2500, "height": 1680},
        description="Rich menu image dimensions",
    )
    selected: bool = Field(default=True, description="Displayed by default")


class RichMenuOut(BaseModel):
    rich_menu_id: str | None = None
    name: str
    chat_bar_text: str
    areas: list[dict]
    selected: bool
    is_default: bool = False


@router.get("/auto-reply", response_model=AutoReplyStatus)
async def get_auto_reply(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current auto-reply toggle state."""
    enabled = await get_auto_reply_setting(db)
    return AutoReplyStatus(enabled=enabled)


@router.put("/auto-reply", response_model=AutoReplyStatus)
async def toggle_auto_reply(
    body: AutoReplyToggleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Enable or disable automatic AI replies to LINE messages."""
    await set_auto_reply_setting(db, body.enabled, current_user.id)
    return AutoReplyStatus(enabled=body.enabled)


@router.get("/rich-menus", response_model=list[RichMenuOut])
async def get_rich_menus(
    current_user: User = Depends(get_current_user),
):
    """List all rich menus from LINE."""
    menus = await list_rich_menus()
    default = await get_default_rich_menu()
    default_id = default.get("richMenuId") if default else None

    out: list[RichMenuOut] = []
    for m in menus:
        out.append(RichMenuOut(
            rich_menu_id=m.get("richMenuId"),
            name=m.get("name", "Unknown"),
            chat_bar_text=m.get("chatBarText", "Menu"),
            areas=m.get("areas", []),
            selected=m.get("selected", False),
            is_default=m.get("richMenuId") == default_id,
        ))
    return out


@router.post("/rich-menus", response_model=RichMenuOut)
async def create_line_rich_menu(
    body: RichMenuCreateRequest,
    current_user: User = Depends(require_admin),
):
    """Create a new rich menu on LINE with the spec-defined 4 actions."""
    menu_config = {
        "size": body.size,
        "selected": body.selected,
        "name": body.name,
        "chatBarText": body.chat_bar_text,
        "areas": body.areas,
    }

    try:
        result = await create_rich_menu(menu_config)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return RichMenuOut(
        rich_menu_id=result.get("richMenuId"),
        name=body.name,
        chat_bar_text=body.chat_bar_text,
        areas=body.areas,
        selected=body.selected,
    )


@router.post("/rich-menus/{rich_menu_id}/set-default")
async def set_default(
    rich_menu_id: str,
    current_user: User = Depends(require_admin),
):
    """Set a rich menu as the default for all LINE users."""
    success = await set_default_rich_menu(rich_menu_id)
    if not success:
        raise HTTPException(status_code=502, detail="line.rich_menu_set_default_failed")
    return {"status": "ok", "rich_menu_id": rich_menu_id, "is_default": True}


@router.post("/rich-menus/{rich_menu_id}/image")
async def upload_rich_menu_image(
    rich_menu_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
):
    """Upload an image for a rich menu (JPEG/PNG, max 1MB).
    Image dimensions must match the rich menu size (default 2500x1680).
    """
    ALLOWED_TYPES = {"image/jpeg", "image/png"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="line.image_type_invalid||allowed=jpeg,png")

    content = await file.read()
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="line.image_too_large||max=1MB")

    try:
        from app.services.line_service import upload_rich_menu_image as _upload
        await _upload(rich_menu_id, content, file.content_type or "image/png")
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {"status": "uploaded", "rich_menu_id": rich_menu_id}


@router.delete("/rich-menus/{rich_menu_id}")
async def remove_rich_menu(
    rich_menu_id: str,
    current_user: User = Depends(require_admin),
):
    """Delete a rich menu from LINE."""
    success = await delete_rich_menu(rich_menu_id)
    if not success:
        raise HTTPException(status_code=502, detail="line.rich_menu_delete_failed")
    return {"status": "deleted", "rich_menu_id": rich_menu_id}
