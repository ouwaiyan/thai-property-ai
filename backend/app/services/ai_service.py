"""AI business-logic service — lead parsing, tagging, sales copy, data cleaning."""
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.property import Property
from app.schemas.ai import (
    CleanDataResponse,
    GenerateTagsResponse,
    ParseLeadResponse,
)
from app.utils.ai_client import simple_chat, structured_completion


async def ai_parse_lead_needs(
    db: AsyncSession, message: str, language: str = "zh"
) -> ParseLeadResponse:
    """Parse a natural-language client message into structured needs using AI."""

    system_prompt_map = {
        "zh": "你是一个泰国房产客户需求分析助手。从客户消息中提取结构化信息。只提取明确提到的内容，不要猜测。",
        "en": "You are a Thai real estate client needs analyzer. Extract structured info from client messages. Only extract explicitly mentioned info, do not guess.",
        "th": "คุณเป็นผู้ช่วยวิเคราะห์ความต้องการของลูกค้าอสังหาริมทรัพย์ไทย ดึงข้อมูลที่มีโครงสร้างจากข้อความของลูกค้า ดึงเฉพาะข้อมูลที่กล่าวถึงอย่างชัดเจน อย่าเดา",
    }

    json_schema = {
        "type": "object",
        "properties": {
            "target_location": {
                "type": ["string", "null"],
                "description": "Desired area, district, BTS/MRT station, or landmark",
            },
            "budget_min": {"type": ["integer", "null"]},
            "budget_max": {"type": ["integer", "null"]},
            "bedroom_count": {"type": ["integer", "null"]},
            "pet_required": {"type": "boolean"},
            "preferred_transport": {
                "type": ["string", "null"],
                "enum": [None, "BTS", "MRT", "walk", "any"],
            },
            "tags": {"type": "array", "items": {"type": "string"}},
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Important fields not mentioned by the client",
            },
            "follow_up_questions": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"2-4 follow-up questions in language code {language} to fill gaps",
            },
        },
        "required": [
            "target_location", "budget_min", "budget_max", "bedroom_count",
            "pet_required", "preferred_transport", "tags",
            "missing_fields", "follow_up_questions",
        ],
        "additionalProperties": False,
    }

    result = await structured_completion(
        system_prompt=system_prompt_map.get(language, system_prompt_map["zh"]),
        user_message=message,
        json_schema=json_schema,
        temperature=0.2,
    )
    return ParseLeadResponse(**result)


async def ai_generate_property_tags(
    db: AsyncSession, property_id: UUID, language: str = "zh"
) -> GenerateTagsResponse:
    """Generate tags and highlights from property facts only — never fabricate."""

    result = await db.execute(
        select(Property).where(Property.id == property_id, Property.is_deleted == False)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise ValueError("property.not_found")

    facts = {
        "name": prop.name,
        "building": getattr(prop, "building_name", None),
        "district": prop.district,
        "area": getattr(prop, "area", None),
        "near_bts": getattr(prop, "nearest_bts", None),
        "near_mrt": getattr(prop, "nearest_mrt", None),
        "bedrooms": prop.bedroom_count,
        "bathrooms": prop.bathroom_count,
        "sqm": prop.size_sqm,
        "rent": prop.monthly_rent,
        "pet_allowed": getattr(prop, "pet_allowed", None),
        "status": prop.status,
        "description": getattr(prop, "description", None),
    }

    lang_map = {"zh": "中文", "en": "English", "th": "ภาษาไทย"}
    target_lang = lang_map.get(language, "Chinese")

    system_prompt = (
        f"You generate property marketing tags and highlights for Thai real estate. "
        f"Output in language: {target_lang}. "
        f"CRITICAL: Only use the provided facts. Do NOT invent features, distances, or amenities. "
        f"Do NOT guess proximity to BTS/MRT unless the fact sheet explicitly lists a station."
    )

    json_schema = {
        "type": "object",
        "properties": {
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "5-8 marketing tags, factual only",
                "minItems": 3,
                "maxItems": 10,
            },
            "highlights": {
                "type": "array",
                "items": {"type": "string"},
                "description": "2-4 one-sentence marketing highlights, factual only",
                "minItems": 1,
                "maxItems": 5,
            },
        },
        "required": ["tags", "highlights"],
        "additionalProperties": False,
    }

    ai_result = await structured_completion(
        system_prompt=system_prompt,
        user_message=json.dumps(facts, ensure_ascii=False),
        json_schema=json_schema,
        temperature=0.4,
    )
    return GenerateTagsResponse(**ai_result)


async def ai_generate_sales_message(
    db: AsyncSession,
    lead: Lead,
    property_ids: list[UUID],
    language: str = "zh",
    tone: str = "friendly",
) -> dict[UUID, str]:
    """Generate personalized sales copy for a lead about specific properties."""

    props_result = await db.execute(
        select(Property).where(Property.id.in_(property_ids))
    )
    props = {p.id: p for p in props_result.scalars().all()}

    tone_map = {
        "friendly": "友好热情的",
        "professional": "专业正式的",
        "urgent": "有紧迫感的",
    }
    lang_map = {"zh": "Chinese", "en": "English", "th": "Thai"}

    messages: dict[UUID, str] = {}
    for pid in property_ids:
        prop = props.get(pid)
        if not prop:
            continue

        facts = {
            "name": prop.name,
            "district": prop.district,
            "rent": prop.monthly_rent,
            "bedrooms": prop.bedroom_count,
            "sqm": prop.size_sqm,
            "near_bts": getattr(prop, "nearest_bts", None),
            "near_mrt": getattr(prop, "nearest_mrt", None),
            "pet_allowed": getattr(prop, "pet_allowed", None),
            "highlights": getattr(prop, "tags", []) or [],
        }

        lead_context = {
            "name": lead.name,
            "budget_range": f"{lead.budget_min}-{lead.budget_max}" if lead.budget_min else "unknown",
            "needs_tags": lead.tags or [],
            "target_location": lead.target_location,
        }

        system_prompt = (
            f"You are a Thai real estate agent. Write a {tone_map.get(tone, 'friendly')} "
            f"property recommendation message in {lang_map.get(language, 'Chinese')}. "
            f"Format: Start with a greeting using the client's name, "
            f"present the property key facts, explain why it matches their needs, "
            f"end with a soft call to action. Be concise (3-5 sentences). "
            f"ONLY use the facts provided — do NOT invent details."
        )

        user_message = (
            f"Client context: {json.dumps(lead_context, ensure_ascii=False)}\n"
            f"Property facts: {json.dumps(facts, ensure_ascii=False)}"
        )

        msg = await simple_chat(system_prompt, user_message, temperature=0.7)
        messages[pid] = msg

    return messages


async def ai_clean_column_data(
    column_name: str, sample_values: list[str], expected_type: str = "auto"
) -> CleanDataResponse:
    """Suggest cleaning rules for a column of dirty data (used during import)."""

    system_prompt = (
        "You are a data cleaning assistant for Thai real estate CSV data. "
        "Given a column name and sample values, suggest cleaning rules or corrections."
    )

    json_schema = {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original": {"type": "string"},
                        "cleaned": {"type": "string"},
                    },
                    "required": ["original", "cleaned"],
                    "additionalProperties": False,
                },
            },
            "pattern_rule": {
                "type": ["string", "null"],
                "description": "Regex pattern suggestion for cleaning",
            },
        },
        "required": ["suggestions", "pattern_rule"],
        "additionalProperties": False,
    }

    user_message = json.dumps({
        "column_name": column_name,
        "expected_type": expected_type,
        "samples": sample_values[:20],
    }, ensure_ascii=False)

    result = await structured_completion(
        system_prompt, user_message, json_schema, temperature=0.2
    )
    return CleanDataResponse(**result)
