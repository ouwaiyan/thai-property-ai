import uuid as _uuid
import os
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.property import Property
from app.models.property_image import PropertyImage
from app.models.user import User
from app.services.storage_service import upload_file, delete_file

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


async def upload_images(
    db: AsyncSession,
    property_id: UUID,
    files: list[UploadFile],
    current_user: User,
) -> list[PropertyImage]:
    # Verify property exists
    result = await db.execute(select(Property).where(Property.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="property.not_found")

    # Agent can only upload to own properties
    if current_user.role == "Agent" and str(prop.created_by) != str(current_user.id):
        raise HTTPException(status_code=403, detail="property.access_denied")

    # Check existing image count for cover/first-image logic
    count_result = await db.execute(
        select(PropertyImage).where(PropertyImage.property_id == property_id)
    )
    existing_count = len(count_result.scalars().all())

    images = []
    for file in files:
        # Validate extension
        ext = os.path.splitext(file.filename or ".jpg")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"property.invalid_file_type||ext={ext}")

        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail=f"property.file_too_large||filename={file.filename}")

        # Upload via storage abstraction (S3 or local)
        try:
            url = await upload_file(content, "properties", file.filename or f"image{ext}")
        except Exception:
            raise HTTPException(status_code=500, detail="property.upload_failed")

        img = PropertyImage(
            property_id=property_id,
            image_url=url,
            sort_order=len(images) + existing_count,
            is_cover=(existing_count == 0 and len(images) == 0),
        )
        db.add(img)
        images.append(img)

    await db.flush()
    return images


async def delete_image(db: AsyncSession, image_id: UUID, current_user: User) -> None:
    result = await db.execute(select(PropertyImage).where(PropertyImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="property.image_not_found")

    # Check property ownership
    prop_result = await db.execute(select(Property).where(Property.id == img.property_id))
    prop = prop_result.scalar_one_or_none()
    if prop and current_user.role == "Agent" and str(prop.created_by) != str(current_user.id):
        raise HTTPException(status_code=403, detail="property.access_denied")

    # Delete from storage
    await delete_file(img.image_url)

    await db.delete(img)
    await db.flush()
