# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
# Backend (Python/FastAPI)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
alembic upgrade head                  # migrate
python seed.py                        # create admin: admin@thaiestate.com / admin123

# Frontend (Next.js)
cd frontend
npm install
npm run dev                           # :3000
npm run build && npm start            # production
npm run lint

# Full stack (Docker)
cp .env.production .env               # edit .env with real keys first
./deploy.sh                           # build + migrate + seed
docker compose up -d                  # start all services
docker compose exec -T backend alembic upgrade head
./backup.sh                           # pg_dump with 30-day retention
```

## Architecture

This is a Thai real-estate AI CRM system: Next.js admin panel → FastAPI REST API → PostgreSQL/PostGIS + Redis → Google Maps + OpenAI + LINE.

### Backend layering

- **`app/api/v1/`** — thin HTTP layer: validation, auth, route to service. Never contains business logic.
- **`app/services/`** — all business logic. Each module gets its own service file (e.g. `recommendation_service.py` handles the full recommendation pipeline from PostGIS filtering through Google Routes to match scoring).
- **`app/models/`** — SQLAlchemy ORM models. Must be registered in `models/__init__.py`.
- **`app/utils/`** — cross-cutting: geo, routing, Redis client, field permissions, i18n.
- **`app/config.py`** — all settings via `pydantic-settings`, reads from `.env`. Access as `from app.config import settings`.
- **`app/database.py`** — async engine + session factory. All DB access is async via `AsyncSession`.

### Key architectural rules

1. **AI never decides facts.** The AI module (`ai_service.py`) only handles language understanding (parse-lead, generate-message, generate-tags) and must only use facts passed from the backend — never fabricate prices, distances, facilities, or pet policies. Distance/time are always suffixed with "约" (approximately) in generated messages.

2. **Caching is always layered.** For both geocoding and route matrix results: try Redis (L1, 30-day TTL) → check database cache table (L2) → call external API (L3). If Redis is down, `redis_client.py` degrades gracefully (all ops become no-ops).

3. **Field-level permissions.** `utils/field_permission.py` masks sensitive fields (`contact_phone`, `contact_line`, `contact_person`, `internal_note`) by role: Admin/Manager see all, Agent sees partial mask (`0812345678` → `081****678`), Viewer sees `null`.

4. **Geocoding fallback chain.** `utils/geo.py`: Google Geocoding API → Nominatim (OSM). Geocoding is cached in-memory, then the `geocode_cache` table. Importing properties without GPS auto-triggers geocoding (max 20). A worker (`worker.py`) scans every 5 minutes for un-geocoded properties.

5. **All new API routers must be registered in `api/v1/router.py`** — import the router and call `api_v1_router.include_router()`.

6. **Audit logging.** All key operations (property CRUD, status changes, API config edits) write to the `audit_logs` table via `services/audit_service.py`. Include before/after JSON.

7. **i18n is everywhere.** Backend: `utils/i18n.py` provides `translate(key, lang)` with `||param=val` parameterized format. Frontend: `src/i18n/{zh,en,th}.json`. Swagger UI at `/docs` has a language switcher (zh/en/th).

### Database

- **PostgreSQL 16 + PostGIS 3.5.** `properties.location_geo` is `geography(Point, 4326)` with GiST index.
- **Migrations:** Alembic in `backend/alembic/versions/`. Create: `alembic revision --autogenerate -m "description"`.
- **Core spatial query pattern** (in `services/recommendation_service.py`): `ST_DWithin(location_geo, ..., radius_meters)` for radius filtering, then `ST_Distance` for sorting, then limit to 50 candidates before calling Google Routes API.

### Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Ant Design Pro Components, react-leaflet, zustand |
| Backend | FastAPI, SQLAlchemy async, Pydantic v2 |
| Database | PostgreSQL 16 + PostGIS 3.5 |
| Cache | Redis 7 (Alpine) |
| AI | OpenAI API (Structured Outputs + JSON Schema) |
| Maps | Google Geocoding/Routes APIs + Nominatim fallback |
| Storage | S3-compatible (boto3), local fallback |
| Messaging | LINE Messaging API |
| Automation | n8n webhooks |

### Docker Compose services

`nginx` (80/443) → `frontend` (:3000) + `backend` (:8000) → `postgres` (:5432), `redis` (:6379), `worker` (background jobs), `n8n` (profile: `full`).

### Testing

No project-level test suite exists yet. The backend uses FastAPI's `TestClient` (via `starlette.testclient`). The frontend uses Next.js defaults. When adding tests:
- Backend: test service functions with a test database, not mocks.
- Frontend: use `next lint` for static analysis.
