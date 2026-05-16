"""
Backend i18n utility for zh/en/th language support.

Provides translation mappings for all user-facing messages (errors, success,
validation).  Works alongside the existing frontend i18n so the API layer
can return messages in the caller's preferred language.

Usage:
    from app.utils.i18n import translate, get_request_language

    lang = get_request_language(request)
    msg = translate("auth.invalid_credentials", lang)
"""

from fastapi import Request

# ---------------------------------------------------------------------------
# Translation dictionaries
# ---------------------------------------------------------------------------
# Key naming convention: "<domain>.<sub_key>", mirroring frontend i18n keys
# where possible so the two stay conceptually aligned.
# ---------------------------------------------------------------------------

_zh = {
    # Auth
    "auth.invalid_credentials": "邮箱或密码错误",
    "auth.account_inactive": "账户已被停用",
    "auth.invalid_token_type": "无效的令牌类型",
    "auth.invalid_token_payload": "无效的令牌负载",
    "auth.user_not_found": "用户不存在",
    "auth.invalid_token": "无效的令牌",
    "auth.logged_out": "已退出登录",
    "auth.insufficient_permissions": "权限不足",
    # Users
    "user.not_found": "用户不存在",
    "user.email_registered": "邮箱已被注册",
    "user.email_in_use": "邮箱已被使用",
    "user.deactivated": "用户已停用",
    # Password validation
    "password.too_short": "密码至少需要8个字符",
    "password.need_letter": "密码必须包含至少一个字母",
    "password.need_digit": "密码必须包含至少一个数字",
    # Properties
    "property.not_found": "房源不存在",
    "property.access_denied": "无权访问此房源",
    "property.code_exists": "房源编号已存在",
    "property.code_in_use": "房源编号已被使用",
    "property.deleted": "房源已删除",
    "property.image_not_found": "图片不存在",
    "property.image_deleted": "图片已删除",
    "property.invalid_file_type": "不支持的文件类型: {ext}",
    "property.file_too_large": "文件过大: {filename}",
    # Leads
    "lead.not_found": "线索不存在",
    # Recommendations
    "recommendation.not_found": "推荐记录不存在",
    # Import
    "import.job_not_found": "导入任务不存在",
    "import.unsupported_type": "不支持的文件类型: {ext}。支持: {allowed}",
    "import.file_too_large": "文件过大，最大 {max_size}MB",
    "import.missing_required": "缺少必填字段: {field}",
    "import.code_duplicate": "房源编号重复: {code}",
    "import.invalid_rent": "月租格式无效: {val}",
    "import.gps_out_of_range": "GPS坐标超出泰国范围: ({lat}, {lng})",
    "import.should_be_int": "{field} 应为整数: {val}",
    "import.should_be_number": "{field} 应为数字: {val}",
    "import.exception": "导入异常: {error}",
    # LINE
    "line.invalid_signature": "无效的签名",
    "line.invalid_json": "无效的JSON格式",
    "line.conversation_not_found": "对话不存在",
    "line.no_incoming_message": "没有找到收到的消息",
    "line.no_lead_associated": "此对话未关联客户线索",
    "line.push_failed": "LINE消息推送失败",
    "line.reply_failed": "LINE消息回复失败",
    "line.channel_token_not_configured": "LINE Channel Access Token 未配置",
    "line.api_error": "LINE API 错误: {status}",
    "line.api_request_failed": "LINE API 请求失败: {error}",
    "line.rich_menu_set_default_failed": "设置默认 Rich Menu 失败",
    "line.rich_menu_delete_failed": "删除 Rich Menu 失败",
    # AI
    "ai.service_unavailable": "AI 服务不可用: OPENAI_API_KEY 未配置",
    "ai.parse_failed": "AI 解析失败: {error}",
    "ai.tag_generation_failed": "标签生成失败: {error}",
    "ai.message_generation_failed": "话术生成失败: {error}",
    "ai.data_cleaning_failed": "数据清洗失败: {error}",
}


_en = {
    # Auth
    "auth.invalid_credentials": "Invalid email or password",
    "auth.account_inactive": "Account is inactive",
    "auth.invalid_token_type": "Invalid token type",
    "auth.invalid_token_payload": "Invalid token payload",
    "auth.user_not_found": "User not found",
    "auth.invalid_token": "Invalid token",
    "auth.logged_out": "Logged out successfully",
    "auth.insufficient_permissions": "Insufficient permissions",
    # Users
    "user.not_found": "User not found",
    "user.email_registered": "Email already registered",
    "user.email_in_use": "Email already in use",
    "user.deactivated": "User deactivated successfully",
    # Password validation
    "password.too_short": "Password must be at least 8 characters",
    "password.need_letter": "Password must contain at least one letter",
    "password.need_digit": "Password must contain at least one digit",
    # Properties
    "property.not_found": "Property not found",
    "property.access_denied": "Access denied",
    "property.code_exists": "Property code already exists",
    "property.code_in_use": "Property code already in use",
    "property.deleted": "Property deleted successfully",
    "property.image_not_found": "Image not found",
    "property.image_deleted": "Image deleted successfully",
    "property.invalid_file_type": "Invalid file type: {ext}",
    "property.file_too_large": "File too large: {filename}",
    # Leads
    "lead.not_found": "Lead not found",
    # Recommendations
    "recommendation.not_found": "Recommendation not found",
    # Import
    "import.job_not_found": "Import job not found",
    "import.unsupported_type": "Unsupported file type: {ext}. Supported: {allowed}",
    "import.file_too_large": "File too large, max {max_size}MB",
    "import.missing_required": "Missing required field: {field}",
    "import.code_duplicate": "Property code duplicate: {code}",
    "import.invalid_rent": "Invalid rent format: {val}",
    "import.gps_out_of_range": "GPS coordinates out of Thailand range: ({lat}, {lng})",
    "import.should_be_int": "{field} should be an integer: {val}",
    "import.should_be_number": "{field} should be a number: {val}",
    "import.exception": "Import exception: {error}",
    # LINE
    "line.invalid_signature": "Invalid signature",
    "line.invalid_json": "Invalid JSON",
    "line.conversation_not_found": "Conversation not found",
    "line.no_incoming_message": "No incoming message found",
    "line.no_lead_associated": "No lead associated with this conversation",
    "line.push_failed": "LINE API push failed",
    "line.reply_failed": "LINE API reply failed",
    "line.channel_token_not_configured": "LINE_CHANNEL_ACCESS_TOKEN not configured",
    "line.api_error": "LINE API error: {status}",
    "line.api_request_failed": "LINE API request failed: {error}",
    "line.rich_menu_set_default_failed": "Failed to set default rich menu",
    "line.rich_menu_delete_failed": "Failed to delete rich menu",
    # AI
    "ai.service_unavailable": "AI service unavailable: OPENAI_API_KEY not configured",
    "ai.parse_failed": "AI parse failed: {error}",
    "ai.tag_generation_failed": "Tag generation failed: {error}",
    "ai.message_generation_failed": "Message generation failed: {error}",
    "ai.data_cleaning_failed": "Data cleaning failed: {error}",
}


_th = {
    # Auth
    "auth.invalid_credentials": "อีเมลหรือรหัสผ่านไม่ถูกต้อง",
    "auth.account_inactive": "บัญชีถูกระงับ",
    "auth.invalid_token_type": "ประเภทโทเค็นไม่ถูกต้อง",
    "auth.invalid_token_payload": "ข้อมูลโทเค็นไม่ถูกต้อง",
    "auth.user_not_found": "ไม่พบผู้ใช้",
    "auth.invalid_token": "โทเค็นไม่ถูกต้อง",
    "auth.logged_out": "ออกจากระบบแล้ว",
    "auth.insufficient_permissions": "สิทธิ์ไม่เพียงพอ",
    # Users
    "user.not_found": "ไม่พบผู้ใช้",
    "user.email_registered": "อีเมลนี้ลงทะเบียนแล้ว",
    "user.email_in_use": "อีเมลนี้ถูกใช้งานแล้ว",
    "user.deactivated": "ระงับผู้ใช้แล้ว",
    # Password validation
    "password.too_short": "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร",
    "password.need_letter": "รหัสผ่านต้องมีตัวอักษรอย่างน้อยหนึ่งตัว",
    "password.need_digit": "รหัสผ่านต้องมีตัวเลขอย่างน้อยหนึ่งตัว",
    # Properties
    "property.not_found": "ไม่พบทรัพย์",
    "property.access_denied": "ไม่มีสิทธิ์เข้าถึง",
    "property.code_exists": "รหัสทรัพย์มีอยู่แล้ว",
    "property.code_in_use": "รหัสทรัพย์ถูกใช้งานแล้ว",
    "property.deleted": "ลบทรัพย์แล้ว",
    "property.image_not_found": "ไม่พบรูปภาพ",
    "property.image_deleted": "ลบรูปภาพแล้ว",
    "property.invalid_file_type": "ประเภทไฟล์ไม่รองรับ: {ext}",
    "property.file_too_large": "ไฟล์ใหญ่เกินไป: {filename}",
    # Leads
    "lead.not_found": "ไม่พบลูกค้า",
    # Recommendations
    "recommendation.not_found": "ไม่พบรายการแนะนำ",
    # Import
    "import.job_not_found": "ไม่พบงานนำเข้า",
    "import.unsupported_type": "ประเภทไฟล์ไม่รองรับ: {ext} รองรับ: {allowed}",
    "import.file_too_large": "ไฟล์ใหญ่เกินไป สูงสุด {max_size}MB",
    "import.missing_required": "ขาดฟิลด์ที่จำเป็น: {field}",
    "import.code_duplicate": "รหัสทรัพย์ซ้ำ: {code}",
    "import.invalid_rent": "รูปแบบค่าเช่าไม่ถูกต้อง: {val}",
    "import.gps_out_of_range": "พิกัด GPS อยู่นอกประเทศไทย: ({lat}, {lng})",
    "import.should_be_int": "{field} ควรเป็นจำนวนเต็ม: {val}",
    "import.should_be_number": "{field} ควรเป็นตัวเลข: {val}",
    "import.exception": "ข้อผิดพลาดนำเข้า: {error}",
    # LINE
    "line.invalid_signature": "ลายเซ็นไม่ถูกต้อง",
    "line.invalid_json": "JSON ไม่ถูกต้อง",
    "line.conversation_not_found": "ไม่พบบทสนทนา",
    "line.no_incoming_message": "ไม่พบข้อความที่ได้รับ",
    "line.no_lead_associated": "บทสนทนานี้ไม่ได้เชื่อมโยงกับลูกค้า",
    "line.push_failed": "การส่งข้อความ LINE ล้มเหลว",
    "line.reply_failed": "การตอบกลับ LINE ล้มเหลว",
    "line.channel_token_not_configured": "ไม่ได้กำหนดค่า LINE_CHANNEL_ACCESS_TOKEN",
    "line.api_error": "ข้อผิดพลาด LINE API: {status}",
    "line.api_request_failed": "คำขอ LINE API ล้มเหลว: {error}",
    "line.rich_menu_set_default_failed": "ตั้งค่า Rich Menu เริ่มต้นล้มเหลว",
    "line.rich_menu_delete_failed": "ลบ Rich Menu ล้มเหลว",
    # AI
    "ai.service_unavailable": "บริการ AI ไม่พร้อมใช้งาน: ไม่ได้กำหนดค่า OPENAI_API_KEY",
    "ai.parse_failed": "การวิเคราะห์ AI ล้มเหลว: {error}",
    "ai.tag_generation_failed": "การสร้างแท็กล้มเหลว: {error}",
    "ai.message_generation_failed": "การสร้างข้อความล้มเหลว: {error}",
    "ai.data_cleaning_failed": "การทำความสะอาดข้อมูลล้มเหลว: {error}",
}

_translations: dict[str, dict[str, str]] = {
    "zh": _zh,
    "en": _en,
    "th": _th,
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

LangCode = str  # "zh" | "en" | "th"


def translate(key: str, lang: LangCode, **params: object) -> str:
    """Translate a message key into the given language.

    Args:
        key: Dot-separated translation key, e.g. "auth.invalid_credentials".
        lang: Language code: "zh", "en", or "th".
        **params: Optional interpolation values for placeholders like {field}.

    Returns:
        The translated string with placeholders filled.
    """
    t = _translations.get(lang, _en)
    text = t.get(key, _en.get(key, key))
    if params:
        for k, v in params.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text


def get_request_language(request: Request) -> LangCode:
    """Detect the preferred language from the incoming request.

    Priority:
        1. ``lang`` query parameter (e.g. ``?lang=th``)
        2. ``Accept-Language`` header
        3. Default ``"en"``
    """
    # Query parameter takes precedence
    qp = request.query_params.get("lang")
    if qp and qp in _translations:
        return qp

    # Parse Accept-Language header
    al = request.headers.get("accept-language", "")
    if al:
        primary = al.split(",")[0].split(";")[0].strip().lower()
        if primary in _translations:
            return primary
        # Match primary language code (e.g. "th-TH" → "th")
        short = primary.split("-")[0]
        if short in _translations:
            return short

    return "en"
