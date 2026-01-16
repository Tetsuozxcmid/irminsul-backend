from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router
from app.core.middleware import auth_middleware,csrf_middleware


import os

APP_ENV = os.getenv("APP_ENV")  

app = FastAPI(
    title="Irminsul",
    description="backend",
    docs_url="/api/docs" if APP_ENV == "dev" else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if APP_ENV == "dev" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")

app.middleware("http")(auth_middleware)
app.middleware("http")(csrf_middleware)





