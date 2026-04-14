from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.auth.routes import vk_router as auth_vk_router
from app.users.routes import router as profile_router
from app.records.routes import router as records_router
from app.files.route import router as file_router
from app.notifications.routes import router as notifications_router

app = FastAPI(
    title="Irminsul",
    description="backend",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://irminsul.space",
        "https://www.irminsul.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)




app.include_router(auth_router, prefix="/api/auth")
app.include_router(auth_vk_router, prefix="/api/auth")
app.include_router(profile_router, prefix="/api")
app.include_router(records_router, prefix="/api/records")
app.include_router(file_router)
app.include_router(notifications_router, prefix="/api")

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}