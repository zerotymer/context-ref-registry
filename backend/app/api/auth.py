from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.auth.dependencies import COOKIE_NAME, AdminDep
from app.config import settings
from app.domain.schemas import OkResponse
from app.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


class LoginRequest(BaseModel):
    login_id: str
    password: str


class AdminRead(BaseModel):
    login_id: str
    role: str = "admin"


def _admin() -> AdminRead:
    return AdminRead(login_id=settings.admin_login_id)


@router.post("/login", response_model=OkResponse[AdminRead])
async def login(body: LoginRequest, response: Response) -> OkResponse[AdminRead]:
    token = auth_service.login(body.login_id, body.password)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=_COOKIE_MAX_AGE,
        secure=False,  # set True behind HTTPS in production
    )
    return OkResponse(data=_admin())


@router.post("/logout", response_model=OkResponse[dict])
async def logout(response: Response) -> OkResponse[dict]:
    response.delete_cookie(key=COOKIE_NAME, httponly=True, samesite="lax")
    return OkResponse(data={"message": "logged out"})


@router.get("/me", response_model=OkResponse[AdminRead])
async def me(_admin_actor: AdminDep) -> OkResponse[AdminRead]:
    return OkResponse(data=_admin())
