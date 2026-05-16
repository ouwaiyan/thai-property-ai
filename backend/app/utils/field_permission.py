"""Field-level permission masking for sensitive property/lead fields.

Masks contact_phone, contact_line, contact_person based on user role:
  Admin / Manager — full access
  Agent           — partial masking (last digits hidden)
  Viewer          — all sensitive fields hidden
"""
import re


SENSITIVE_FIELDS = {"contact_phone", "contact_line", "contact_person", "internal_note"}


def mask_phone(phone: str | None) -> str | None:
    """Mask middle portion of phone number: 0812345678 → 081****678"""
    if not phone:
        return None
    cleaned = re.sub(r"[^\d]", "", phone)
    if len(cleaned) <= 4:
        return "****"
    return cleaned[:3] + "****" + cleaned[-3:]


def mask_line_id(line_id: str | None) -> str | None:
    """Mask LINE ID: john_doe123 → joh****123"""
    if not line_id:
        return None
    if len(line_id) <= 4:
        return "****"
    return line_id[:3] + "****" + line_id[-3:]


def mask_contact_person(name: str | None) -> str | None:
    """Mask contact person name: Somchai → Som****"""
    if not name:
        return None
    if len(name) <= 2:
        return "**"
    return name[:3] + "****"


def apply_field_permissions(data: dict, role: str) -> dict:
    """Apply field-level masking to a property/lead dict based on role.

    Returns a modified copy — does not mutate the original.
    """
    if role in ("Admin", "Manager"):
        return data

    result = dict(data)

    if role == "Agent":
        if "contact_phone" in result and result["contact_phone"]:
            result["contact_phone"] = mask_phone(result["contact_phone"])
        if "contact_line" in result and result["contact_line"]:
            result["contact_line"] = mask_line_id(result["contact_line"])
        if "contact_person" in result and result["contact_person"]:
            result["contact_person"] = mask_contact_person(result["contact_person"])
        # Agent can see internal_note
    elif role == "Viewer":
        for field in SENSITIVE_FIELDS:
            if field in result:
                result[field] = None

    return result
