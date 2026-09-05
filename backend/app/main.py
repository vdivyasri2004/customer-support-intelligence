from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.routes import auth, datasets, tickets, analytics, ai_routes, history

settings = get_settings()

app = FastAPI(
    title="Customer Support Intelligence",
    description="Analytics platform for customer support ticket analysis",
    version="1.0.0",
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(tickets.router)
app.include_router(analytics.router)
app.include_router(ai_routes.router)
app.include_router(history.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
