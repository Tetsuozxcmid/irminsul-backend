from fastapi import APIRouter

router = APIRouter(tags=["Profile interaction"])

@router.get("/profile")
async def hello_world():
    return {"message": "Hello World from profile!"}