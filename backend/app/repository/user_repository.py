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

    async def list_all(
        self,
        *,
        role: str | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[UserAccount]:
        from sqlalchemy import and_, func as sqlfunc

        conditions = []
        if role is not None:
            conditions.append(UserAccount.role == role)
        if is_active is not None:
            conditions.append(UserAccount.is_active.is_(is_active))
        if search:
            conditions.append(UserAccount.email.ilike(f"%{search}%"))

        stmt = select(UserAccount)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(sqlfunc.lower(UserAccount.email))
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def update(
        self,
        user: UserAccount,
        *,
        display_name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        password_hash: str | None = None,
    ) -> UserAccount:
        if display_name is not None:
            user.display_name = display_name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if password_hash is not None:
            user.password_hash = password_hash
        await self._session.flush()
        await self._session.refresh(user)
        return user
