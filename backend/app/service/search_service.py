from app.domain.enums import EntityType
from app.domain.models import Entity
from app.repository.entity_repository import EntityRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = EntityRepository(session)

    async def search(
        self,
        query: str,
        types: list[EntityType] | None = None,
        limit: int = 10,
    ) -> list[tuple[Entity, str]]:
        return await self._repo.search(query, types, limit)
