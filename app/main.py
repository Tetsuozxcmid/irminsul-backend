from fastapi import FastAPI
from app.auth.routes import router as auth_router

app = FastAPI(title='Irminsul', description='Test backend')


@app.get("/")
async def root():
    return {"message": "Welcome to Irminsul!"}


app.include_router(auth_router, prefix="/auth")
