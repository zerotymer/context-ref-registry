from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import UserAccount


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> UserAccount | None:
        result = await self._session.execute(
            select(UserAccount).where(UserAccount.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserAccount | None:
        result = await self._session.execute(
            select(UserAccount).where(UserAccount.email == email)
        )
        return result.scalar_one_or_none()

    async def exists_admin(self) -> bool:
        result = await self._session.execute(
            select(UserAccount).where(UserAccount.role == "admin").limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
        role: str = "user",
        created_by: uuid.UUID | None = None,
    ) -> UserAccount:
        user = UserAccount(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
            created_by=created_by,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
