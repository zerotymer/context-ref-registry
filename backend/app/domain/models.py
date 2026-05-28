import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Entity(Base):
    __tablename__ = "entity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    replacement_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"))
    deprecation_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[list["EntityAlias"]] = relationship("EntityAlias", back_populates="entity", lazy="selectin")
    contexts: Mapped[list["EntityContext"]] = relationship("EntityContext", back_populates="entity", lazy="selectin")
    tags: Mapped[list["EntityTag"]] = relationship("EntityTag", back_populates="entity", lazy="selectin")
    metadata_entries: Mapped[list["EntityMetadata"]] = relationship(
        "EntityMetadata", back_populates="entity", lazy="selectin"
    )
    outgoing_relations: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation", foreign_keys="EntityRelation.from_entity_id", back_populates="from_entity", lazy="selectin"
    )
    incoming_relations: Mapped[list["EntityRelation"]] = relationship(
        "EntityRelation", foreign_keys="EntityRelation.to_entity_id", back_populates="to_entity", lazy="selectin"
    )


class EntityAlias(Base):
    __tablename__ = "entity_alias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="aliases")


class EntityTag(Base):
    __tablename__ = "entity_tag"
    __table_args__ = (UniqueConstraint("entity_id", "tag", name="uq_entity_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="tags")


class EntityContext(Base):
    __tablename__ = "entity_context"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="ko")
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_ref.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    entity: Mapped["Entity"] = relationship("Entity", back_populates="contexts")
    source_ref: Mapped["SourceRef | None"] = relationship("SourceRef")


class EntityRelation(Base):
    __tablename__ = "entity_relation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    from_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False, index=True
    )
    to_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    from_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[from_entity_id], back_populates="outgoing_relations"
    )
    to_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[to_entity_id], back_populates="incoming_relations"
    )


class EntityMetadata(Base):
    __tablename__ = "entity_metadata"
    __table_args__ = (UniqueConstraint("entity_id", "meta_type", name="uq_entity_metadata_type"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False)
    meta_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    entity: Mapped["Entity"] = relationship("Entity", back_populates="metadata_entries")


class SourceRef(Base):
    __tablename__ = "source_ref"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    uri: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(100))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
