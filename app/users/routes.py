from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.users.schemas import UserProfileOut, UserProfileUpdate
from app.users.service import UserProfileService
from app.users.dependency import get_current_user
from app.auth.models import User

router = APIRouter(
    prefix="/users",
    tags=["Profile interaction"],
)


@router.get("/profile", response_model=UserProfileOut)
async def get_my_profile(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await UserProfileService.get_profile(
        session=session,
        user=user,
    )


@router.patch("/profile", response_model=UserProfileOut)
async def update_my_profile(
    data: UserProfileUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await UserProfileService.update_profile(
        session=session,
        user=user,
        data=data,
    )
