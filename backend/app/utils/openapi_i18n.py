"""
OpenAPI schema i18n — translates tags, summaries, and descriptions
in the generated OpenAPI JSON based on the requested language.

Integration (in main.py):

    from app.utils.openapi_i18n import patch_openapi_for_language

    # Override the default /openapi.json to accept ?lang=
    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_lang(request: Request):
        lang = get_request_language(request)
        schema = app.openapi()  # force generation if not cached
        return patch_openapi_for_language(schema, lang)
"""

from app.utils.i18n import _translations  # noqa: F401  # used by lang_map

# ---------------------------------------------------------------------------
# Tag name translations (English originals → zh / th)
# ---------------------------------------------------------------------------
TAG_I18N: dict[str, dict[str, str]] = {
    "Auth":       {"zh": "认证",       "en": "Auth",       "th": "การยืนยันตัวตน"},
    "Users":      {"zh": "用户管理",   "en": "Users",      "th": "จัดการผู้ใช้"},
    "Properties": {"zh": "房源管理",   "en": "Properties", "th": "จัดการทรัพย์"},
    "Audit Logs": {"zh": "审计日志",   "en": "Audit Logs", "th": "บันทึกการตรวจสอบ"},
    "Imports":    {"zh": "导入管理",   "en": "Imports",    "th": "นำเข้าข้อมูล"},
    "Geo":        {"zh": "地理编码",   "en": "Geo",        "th": "พิกัดภูมิศาสตร์"},
    "Transit":    {"zh": "交通路线",   "en": "Transit",    "th": "การเดินทาง"},
    "AI":         {"zh": "AI 工具",    "en": "AI",         "th": "เครื่องมือ AI"},
    "Leads":      {"zh": "客户线索",   "en": "Leads",      "th": "ลูกค้า"},
    "LINE":       {"zh": "LINE 消息",  "en": "LINE",       "th": "ข้อความ LINE"},
    "LINE Settings": {"zh": "LINE 设置", "en": "LINE Settings", "th": "ตั้งค่า LINE"},
    "Recommendations": {"zh": "推荐引擎", "en": "Recommendations", "th": "คำแนะนำ"},
    "n8n":        {"zh": "n8n 工作流", "en": "n8n",        "th": "n8n เวิร์กโฟลว์"},
    "Reports":    {"zh": "数据报表",   "en": "Reports",    "th": "รายงาน"},
}

# ---------------------------------------------------------------------------
# Operation description translations (by path + method)
# ---------------------------------------------------------------------------
OPERATION_I18N: dict[str, dict[str, dict[str, str]]] = {
    # Auth
    "POST /api/v1/auth/login": {
        "zh": "用户登录，返回 access/refresh token",
        "en": "User login — returns access/refresh token pair",
        "th": "เข้าสู่ระบบ — ส่งคืน access/refresh token",
    },
    "POST /api/v1/auth/refresh": {
        "zh": "使用 refresh token 刷新 access token",
        "en": "Refresh access token using refresh token",
        "th": "รีเฟรช access token โดยใช้ refresh token",
    },
    "GET /api/v1/auth/me": {
        "zh": "获取当前登录用户信息",
        "en": "Get current logged-in user profile",
        "th": "ดูข้อมูลผู้ใช้ที่เข้าสู่ระบบ",
    },
    "POST /api/v1/auth/logout": {
        "zh": "退出登录",
        "en": "Logout current session",
        "th": "ออกจากระบบ",
    },
    # Users
    "GET /api/v1/users/": {
        "zh": "分页获取用户列表，支持搜索与筛选",
        "en": "List users with pagination, search and filter support",
        "th": "รายชื่อผู้ใช้ พร้อมการค้นหาและกรอง",
    },
    "POST /api/v1/users/": {
        "zh": "创建新用户",
        "en": "Create a new user",
        "th": "สร้างผู้ใช้ใหม่",
    },
    "GET /api/v1/users/{user_id}": {
        "zh": "获取单个用户详情",
        "en": "Get user detail by ID",
        "th": "ดูรายละเอียดผู้ใช้ตาม ID",
    },
    "PUT /api/v1/users/{user_id}": {
        "zh": "更新用户信息",
        "en": "Update user information",
        "th": "อัปเดตข้อมูลผู้ใช้",
    },
    "DELETE /api/v1/users/{user_id}": {
        "zh": "停用用户（软删除）",
        "en": "Deactivate user (soft delete)",
        "th": "ระงับผู้ใช้ (ลบแบบซอฟต์)",
    },
    # Properties
    "GET /api/v1/properties/": {
        "zh": "分页获取房源列表，支持多条件筛选与空间搜索",
        "en": "List properties with pagination, filtering and spatial search",
        "th": "รายชื่อทรัพย์ พร้อมการกรองและค้นหาตามตำแหน่ง",
    },
    "POST /api/v1/properties/": {
        "zh": "创建新房源",
        "en": "Create a new property",
        "th": "สร้างทรัพย์ใหม่",
    },
    "GET /api/v1/properties/{property_id}": {
        "zh": "获取房源详情",
        "en": "Get property detail by ID",
        "th": "ดูรายละเอียดทรัพย์ตาม ID",
    },
    "PUT /api/v1/properties/{property_id}": {
        "zh": "更新房源信息",
        "en": "Update property information",
        "th": "อัปเดตข้อมูลทรัพย์",
    },
    "DELETE /api/v1/properties/{property_id}": {
        "zh": "软删除房源",
        "en": "Soft-delete a property",
        "th": "ลบทรัพย์ (แบบซอฟต์)",
    },
    "POST /api/v1/properties/{property_id}/images": {
        "zh": "上传房源图片",
        "en": "Upload images for a property",
        "th": "อัปโหลดรูปภาพสำหรับทรัพย์",
    },
    "DELETE /api/v1/properties/images/{image_id}": {
        "zh": "删除房源图片",
        "en": "Delete a property image",
        "th": "ลบรูปภาพทรัพย์",
    },
    # Audit Logs
    "GET /api/v1/audit-logs/": {
        "zh": "分页获取审计日志",
        "en": "List audit logs with pagination",
        "th": "รายการบันทึกการตรวจสอบ",
    },
    "GET /api/v1/audit-logs/{log_id}": {
        "zh": "获取单条审计日志详情",
        "en": "Get audit log detail",
        "th": "ดูรายละเอียดบันทึกการตรวจสอบ",
    },
    # Imports
    "POST /api/v1/imports/upload": {
        "zh": "上传 CSV/Excel 文件",
        "en": "Upload a CSV/Excel file for import",
        "th": "อัปโหลดไฟล์ CSV/Excel",
    },
    "GET /api/v1/imports/{import_job_id}/columns": {
        "zh": "获取上传文件的列名及自动检测字段",
        "en": "Get file columns and auto-detected fields",
        "th": "ดูคอลัมน์ไฟล์และฟิลด์ที่ตรวจพบ",
    },
    "GET /api/v1/imports/{import_job_id}/preview": {
        "zh": "预览导入数据（含验证错误）",
        "en": "Preview import data with validation errors",
        "th": "ดูตัวอย่างข้อมูลนำเข้าพร้อมข้อผิดพลาด",
    },
    "POST /api/v1/imports/{import_job_id}/map": {
        "zh": "映射列名到房源字段",
        "en": "Map source columns to property fields",
        "th": "จับคู่คอลัมน์กับฟิลด์ทรัพย์",
    },
    "POST /api/v1/imports/{import_job_id}/confirm": {
        "zh": "确认并执行导入",
        "en": "Confirm and execute import",
        "th": "ยืนยันและดำเนินการนำเข้า",
    },
    "GET /api/v1/imports/": {
        "zh": "获取导入任务列表",
        "en": "List import jobs",
        "th": "รายการงานนำเข้า",
    },
    "GET /api/v1/imports/{import_job_id}": {
        "zh": "获取导入任务详情",
        "en": "Get import job detail",
        "th": "ดูรายละเอียดงานนำเข้า",
    },
    "GET /api/v1/imports/{import_job_id}/errors": {
        "zh": "获取导入错误明细",
        "en": "Get import error details",
        "th": "ดูรายละเอียดข้อผิดพลาดการนำเข้า",
    },
    # Geo
    "GET /api/v1/geo/geocode": {
        "zh": "地址→经纬度 解析",
        "en": "Forward geocoding — address to coordinates",
        "th": "แปลงที่อยู่เป็นพิกัด",
    },
    "GET /api/v1/geo/reverse": {
        "zh": "经纬度→地址 逆解析",
        "en": "Reverse geocoding — coordinates to address",
        "th": "แปลงพิกัดเป็นที่อยู่",
    },
    "GET /api/v1/geo/nearby": {
        "zh": "搜索附近地点",
        "en": "Search nearby places",
        "th": "ค้นหาสถานที่ใกล้เคียง",
    },
    # Transit
    "POST /api/v1/transit/routes": {
        "zh": "计算两点间的交通路线",
        "en": "Compute transit routes between two points",
        "th": "คำนวณเส้นทางระหว่างสองจุด",
    },
    # AI
    "POST /api/v1/ai/parse-lead": {
        "zh": "AI 解析客户原始消息为结构化需求",
        "en": "AI-parse raw client message into structured needs",
        "th": "AI วิเคราะห์ข้อความลูกค้าเป็นความต้องการที่มีโครงสร้าง",
    },
    "POST /api/v1/ai/generate-tags": {
        "zh": "AI 为房源生成营销标签与亮点",
        "en": "AI-generate marketing tags and highlights for a property",
        "th": "AI สร้างแท็กการตลาดและจุดเด่นสำหรับทรัพย์",
    },
    "POST /api/v1/ai/generate-message": {
        "zh": "AI 为房源生成个性化销售话术",
        "en": "AI-generate personalized sales copy for properties",
        "th": "AI สร้างข้อความขายส่วนบุคคลสำหรับทรัพย์",
    },
    "POST /api/v1/ai/clean-data": {
        "zh": "AI 数据清洗建议",
        "en": "AI-assisted data cleaning suggestions",
        "th": "AI แนะนำการทำความสะอาดข้อมูล",
    },
    # Leads
    "GET /api/v1/leads/": {
        "zh": "分页获取客户线索列表",
        "en": "List leads with pagination and filtering",
        "th": "รายชื่อลูกค้า พร้อมการกรอง",
    },
    "POST /api/v1/leads/": {
        "zh": "创建新客户线索",
        "en": "Create a new lead",
        "th": "สร้างลูกค้าใหม่",
    },
    "GET /api/v1/leads/{lead_id}": {
        "zh": "获取客户线索详情",
        "en": "Get lead detail by ID",
        "th": "ดูรายละเอียดลูกค้า",
    },
    "PUT /api/v1/leads/{lead_id}": {
        "zh": "更新客户线索",
        "en": "Update lead information",
        "th": "อัปเดตข้อมูลลูกค้า",
    },
    "POST /api/v1/leads/{lead_id}/parse": {
        "zh": "AI 解析线索需求",
        "en": "AI-parse lead needs from original message",
        "th": "AI วิเคราะห์ความต้องการลูกค้า",
    },
    # LINE
    "POST /api/v1/line/webhook": {
        "zh": "LINE 官方号 Webhook 接收端",
        "en": "LINE Messaging API webhook endpoint",
        "th": "จุดรับ Webhook ของ LINE Messaging API",
    },
    "GET /api/v1/line/conversations": {
        "zh": "获取 LINE 对话列表",
        "en": "List LINE conversations",
        "th": "รายการสนทนา LINE",
    },
    "GET /api/v1/line/conversations/{line_user_id}": {
        "zh": "获取单个 LINE 对话详情",
        "en": "Get LINE conversation detail",
        "th": "ดูรายละเอียดการสนทนา LINE",
    },
    "POST /api/v1/line/conversations/{line_user_id}/ai-reply": {
        "zh": "AI 生成建议回复",
        "en": "Generate AI reply suggestion for conversation",
        "th": "AI สร้างข้อความแนะนำสำหรับการตอบกลับ",
    },
    "POST /api/v1/line/push": {
        "zh": "主动推送 LINE 消息",
        "en": "Push a message to a LINE user",
        "th": "ส่งข้อความแบบ Push ไปยังผู้ใช้ LINE",
    },
    "POST /api/v1/line/reply": {
        "zh": "回复 LINE 消息",
        "en": "Reply to a LINE message",
        "th": "ตอบกลับข้อความ LINE",
    },
    # LINE Settings
    "GET /api/v1/line/settings/auto-reply": {
        "zh": "获取自动回复开关状态",
        "en": "Get auto-reply toggle state",
        "th": "ดูสถานะการตอบกลับอัตโนมัติ",
    },
    "PUT /api/v1/line/settings/auto-reply": {
        "zh": "设置自动回复开关",
        "en": "Enable/disable automatic AI replies",
        "th": "เปิด/ปิดการตอบกลับอัตโนมัติ",
    },
    "GET /api/v1/line/settings/rich-menus": {
        "zh": "获取 LINE Rich Menu 列表",
        "en": "List LINE rich menus",
        "th": "รายการ Rich Menu ของ LINE",
    },
    "POST /api/v1/line/settings/rich-menus": {
        "zh": "创建 LINE Rich Menu",
        "en": "Create a LINE rich menu",
        "th": "สร้าง Rich Menu บน LINE",
    },
    "POST /api/v1/line/settings/rich-menus/{rich_menu_id}/set-default": {
        "zh": "设为默认 Rich Menu",
        "en": "Set a rich menu as default for all users",
        "th": "ตั้งเป็น Rich Menu เริ่มต้น",
    },
    "DELETE /api/v1/line/settings/rich-menus/{rich_menu_id}": {
        "zh": "删除 LINE Rich Menu",
        "en": "Delete a LINE rich menu",
        "th": "ลบ Rich Menu",
    },
    # Recommendations
    "POST /api/v1/recommendations/search": {
        "zh": "基于客户需求搜索匹配房源并评分",
        "en": "Search and score properties against lead needs",
        "th": "ค้นหาและให้คะแนนทรัพย์ตามความต้องการของลูกค้า",
    },
    "GET /api/v1/recommendations/by-lead/{lead_id}": {
        "zh": "获取某线索的推荐历史",
        "en": "Get recommendation history for a lead",
        "th": "ดูประวัติคำแนะนำสำหรับลูกค้า",
    },
    "POST /api/v1/recommendations/{recommendation_id}/save-message": {
        "zh": "保存 AI 生成话术到推荐记录",
        "en": "Save AI-generated message to recommendation",
        "th": "บันทึกข้อความ AI ลงในคำแนะนำ",
    },
    "POST /api/v1/recommendations/{recommendation_id}/mark-sent": {
        "zh": "标记推荐已发送",
        "en": "Mark recommendation as sent to customer",
        "th": "ทำเครื่องหมายว่าส่งให้ลูกค้าแล้ว",
    },
    # n8n
    "GET /api/v1/n8n/webhooks/": {
        "zh": "获取 n8n webhook 触发记录",
        "en": "List n8n webhook trigger records",
        "th": "รายการบันทึก n8n webhook",
    },
    "POST /api/v1/n8n/webhooks/{trigger_id}/retry": {
        "zh": "重试失败的 n8n webhook",
        "en": "Retry failed n8n webhook",
        "th": "ลองใหม่ n8n webhook ที่ล้มเหลว",
    },
    # Reports
    "GET /api/v1/reports/overview": {
        "zh": "报表总览 — 关键 KPI 数据",
        "en": "Reports overview — key KPI data",
        "th": "ภาพรวมรายงาน — ข้อมูล KPI สำคัญ",
    },
    "GET /api/v1/reports/top-properties": {
        "zh": "热门房源排名",
        "en": "Top properties ranking",
        "th": "จัดอันดับทรัพย์ยอดนิยม",
    },
    "GET /api/v1/reports/daily-trends": {
        "zh": "每日趋势数据",
        "en": "Daily trend data",
        "th": "ข้อมูลแนวโน้มรายวัน",
    },
}

# ---------------------------------------------------------------------------
# Patching function
# ---------------------------------------------------------------------------


def patch_openapi_for_language(schema: dict, lang: str) -> dict:
    """Translate tag names and operation descriptions in-place."""
    if lang == "en":
        return schema  # source language, no-op

    # Translate tags
    for tag in schema.get("tags", []):
        name = tag.get("name", "")
        if name in TAG_I18N:
            translated = TAG_I18N[name].get(lang)
            if translated:
                tag["name"] = translated

    # Translate operation descriptions
    for _path, methods in schema.get("paths", {}).items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue
            op_key = f"{method.upper()} {_path}"
            if op_key in OPERATION_I18N:
                trans = OPERATION_I18N[op_key].get(lang)
                if trans:
                    # summary: short label shown next to path
                    operation["summary"] = trans
                    # Also update description if not already set
                    if not operation.get("description"):
                        operation["description"] = trans

            # Translate tag names inside each operation
            op_tags = operation.get("tags", [])
            for i, t in enumerate(op_tags):
                if t in TAG_I18N:
                    translated = TAG_I18N[t].get(lang)
                    if translated:
                        op_tags[i] = translated

    return schema
