import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.config import settings
from app.utils.i18n import get_request_language, translate
from app.utils.openapi_i18n import patch_openapi_for_language

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        debug=settings.DEBUG,
        docs_url=None,   # custom /docs below with i18n support
        redoc_url=None,  # custom /redoc below with i18n support
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.DEBUG:
            response.headers["Cache-Control"] = "no-store"
        return response

    # Global exception handler — translates HTTPException.detail via i18n
    @app.exception_handler(HTTPException)
    async def i18n_exception_handler(request: Request, exc: HTTPException):
        lang = get_request_language(request)
        detail = exc.detail
        # Parameterized keys use "key||param1=val1||param2=val2" format
        if "||" in detail:
            parts = detail.split("||")
            key = parts[0]
            params: dict[str, object] = {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    params[k] = v
            detail = translate(key, lang, **params)
        else:
            detail = translate(detail, lang)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
            headers=exc.headers if hasattr(exc, "headers") else None,
        )

    app.include_router(api_v1_router, prefix="/api/v1")

    # ── Multilingual Swagger / OpenAPI ────────────────────────────────
    # Override openapi.json to accept ?lang= query param
    _base_openapi = app.openapi

    @app.get("/openapi.json", include_in_schema=False)
    async def openapi_i18n(request: Request):
        lang = get_request_language(request)
        schema = _base_openapi()
        return patch_openapi_for_language(schema, lang)

    # Custom Swagger UI with language switcher injected
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_docs(request: Request):
        lang = get_request_language(request)
        swagger_css = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
        swagger_js = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
        spec_url = f"/openapi.json?lang={lang}"

        html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.APP_NAME} - API Docs</title>
    <link rel="stylesheet" href="{swagger_css}">
    <style>
      .lang-bar {{
        display: flex; align-items: center; gap: 8px;
        padding: 8px 16px; background: #1b1b1b; color: #ccc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 13px;
      }}
      .lang-bar select {{
        padding: 4px 8px; border-radius: 4px; border: 1px solid #555;
        background: #2b2b2b; color: #eee; font-size: 13px; cursor: pointer;
      }}
      .lang-bar a {{ color: #7cb8ff; text-decoration: none; margin-left: 8px; }}
      .lang-bar a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="lang-bar">
        <span>Language / 语言 / ภาษา:</span>
        <select id="lang-select" onchange="switchLang(this.value)">
            <option value="zh" {'selected' if lang == 'zh' else ''}>中文</option>
            <option value="en" {'selected' if lang == 'en' else ''}>English</option>
            <option value="th" {'selected' if lang == 'th' else ''}>ไทย</option>
        </select>
        <span style="flex:1"></span>
        <a href="/redoc?lang={lang}">ReDoc</a>
        <a href="/">Home</a>
    </div>
    <div id="swagger-ui"></div>
    <script src="{swagger_js}"></script>
    <script>
    function switchLang(lang) {{
        var url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.location = url;
    }}
    SwaggerUIBundle({{
        url: "{spec_url}",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
        layout: "StandaloneLayout",
    }});
    </script>
</body>
</html>"""
        return HTMLResponse(html)

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_docs(request: Request):
        lang = get_request_language(request)
        redoc_js = "https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"

        html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.APP_NAME} - API Docs (ReDoc)</title>
    <style>
      .lang-bar {{
        display: flex; align-items: center; gap: 8px;
        padding: 8px 16px; background: #1b1b1b; color: #ccc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 13px;
      }}
      .lang-bar select {{
        padding: 4px 8px; border-radius: 4px; border: 1px solid #555;
        background: #2b2b2b; color: #eee; font-size: 13px; cursor: pointer;
      }}
      .lang-bar a {{ color: #7cb8ff; text-decoration: none; margin-left: 8px; }}
    </style>
</head>
<body>
    <div class="lang-bar">
        <span>Language / 语言 / ภาษา:</span>
        <select onchange="switchLang(this.value)">
            <option value="zh" {'selected' if lang == 'zh' else ''}>中文</option>
            <option value="en" {'selected' if lang == 'en' else ''}>English</option>
            <option value="th" {'selected' if lang == 'th' else ''}>ไทย</option>
        </select>
        <span style="flex:1"></span>
        <a href="/docs?lang={lang}">Swagger</a>
        <a href="/">Home</a>
    </div>
    <div id="redoc-container"></div>
    <script src="{redoc_js}"></script>
    <script>
    function switchLang(lang) {{
        var url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.location = url;
    }}
    Redoc.init(
        "/openapi.json?lang={lang}",
        {{ nativeScrollbars: true }},
        document.getElementById("redoc-container")
    );
    </script>
</body>
</html>"""
        return HTMLResponse(html)

    # Serve uploaded files
    uploads_path = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(uploads_path, exist_ok=True)
    app.mount("/static/properties", StaticFiles(directory=uploads_path), name="property_images")

    imports_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, "..", "imports"))
    os.makedirs(imports_path, exist_ok=True)
    app.mount("/static/imports", StaticFiles(directory=imports_path), name="import_files")

    # Startup safety check
    @app.on_event("startup")
    async def startup_check():
        issues = []
        if settings.DEBUG:
            issues.append("DEBUG=True — 生产环境请设为 false")
        if settings.JWT_SECRET_KEY == "change-me-in-production-use-256-bit-key-thai-estate":
            issues.append("JWT_SECRET_KEY 为默认值 — 请更换为随机密钥")
        if not settings.OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY 未配置 — AI 功能将不可用")
        if not settings.GOOGLE_MAPS_API_KEY:
            logger.info("GOOGLE_MAPS_API_KEY 未配置 — 地图功能将不可用")
        for issue in issues:
            logger.warning(f"[SECURITY] {issue}")
        if issues:
            msg = " | ".join(issues)
            logger.warning(f"启动安全检查发现问题: {msg}")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/")
    async def root():
        return HTMLResponse("""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ThaiEstate API</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f0f2f5; }
  .card { background: white; border-radius: 12px; padding: 48px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); text-align: center; max-width: 500px; }
  h1 { color: #1677ff; margin: 0 0 12px; }
  p { color: #666; line-height: 1.8; margin: 0 0 24px; }
  .links { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
  a { display: inline-block; padding: 10px 24px; border-radius: 6px; text-decoration: none; font-weight: 500; }
  .btn-primary { background: #1677ff; color: white; }
  .btn-secondary { border: 1px solid #d9d9d9; color: #333; }
</style>
</head>
<body>
<div class="card">
  <h1>ThaiEstate API</h1>
  <p>后端 API 服务已启动。后台管理面板请访问前端地址。</p>
  <div class="links">
    <a class="btn-primary" href="http://localhost:3000">管理后台 (端口 3000)</a>
    <a class="btn-secondary" href="/docs">API 文档</a>
  </div>
</div>
</body>
</html>
        """)

    return app


app = create_app()
