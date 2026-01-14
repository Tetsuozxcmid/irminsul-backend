from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import YandexCodeSchema
from app.db.session import get_db
from app.auth.service import AuthService

router = APIRouter(prefix="/yandex", tags=["OAuth"])

@router.post("/callback")
async def yandex_callback(
    data: YandexCodeSchema,
    session: AsyncSession = Depends(get_db),
):
    try:
        result = await AuthService.yandex_callback(
            session=session,
            code=data.code,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = JSONResponse(content=result["payload"])
    for k, v in result["cookies"].items():
        response.headers[k] = v


    payload = result["payload"].copy()
    payload["type"] = result["type"]
    response.body = JSONResponse(content=payload).body

    return response

