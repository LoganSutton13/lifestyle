from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from app.api.error_handlers import register_error_handlers
from app.api.routers import admin, auth, checklist, coach, me, meals, measurements
from app.core.cors import configure_cors

app = FastAPI(title="Fitness Coaching API", version="1.0.0", default_response_class=ORJSONResponse)

configure_cors(app)
register_error_handlers(app)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(me.router, prefix="/api/me", tags=["me"])
app.include_router(meals.router, prefix="/api/me/meals", tags=["client meals"])
app.include_router(measurements.router, prefix="/api/me", tags=["client measurements"])
app.include_router(checklist.router, prefix="/api/me", tags=["client checklist"])
app.include_router(coach.router, prefix="/api/coach", tags=["coach"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
