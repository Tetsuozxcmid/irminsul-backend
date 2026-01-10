from fastapi import APIRouter

router = APIRouter(tags=["Auth services"])

@router.get("/hello")
async def hello_world():
    return {"message": "Hello World from auth!"}
