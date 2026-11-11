import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class UtcDateTime(TypeDecorator):
    """Timezone-aware UTC datetime on top of a naive DB column.

    SQLite drops tzinfo, so values are stored as naive UTC and tagged with
    UTC on read. Naive inputs are assumed to already be UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return value.replace(tzinfo=UTC) if value is not None else None


class Base(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Project(Base):
    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    alias: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=func.now()
    )


class Entity(Base):
    __tablename__ = "entity"
    # short_seq: per-(project, type) running number for the short identifier
    # PROJECT_ID-TYPE-N. NULL when project_id is absent (no short id assigned).
    __table_args__ = (
        UniqueConstraint("project_id", "type", "short_seq", name="uq_entity_short_seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="candidate", index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    replacement_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("entity.id"))
    deprecation_reason: Mapped[str | None] = mapped_column(Text)
    project_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("project.id"), nullable=True, index=True)
    short_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=func.now()
    )

    @property
    def short_id(self) -> str | None:
        """Derived short identifier PROJECT_ID-TYPE-N (None when unscoped)."""
        if self.project_id is None or self.short_seq is None:
            return None
        type_val = self.type.value if hasattr(self.type, "value") else self.type
        return f"{self.project_id}-{type_val}-{self.short_seq}"

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
    history: Mapped[list["EntityHistory"]] = relationship(
        "EntityHistory", back_populates="entity", lazy="noload"
    )


class EntityAlias(Base):
    __tablename__ = "entity_alias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("entity.id"), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="aliases")


class EntityTag(Base):
    __tablename__ = "entity_tag"
    __table_args__ = (UniqueConstraint("entity_id", "tag", name="uq_entity_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="tags")


class EntityContext(Base):
    __tablename__ = "entity_context"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("entity.id"), nullable=False)
    context_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="ko")
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("source_ref.id"))
    project_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("project.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=func.now()
    )

    entity: Mapped["Entity"] = relationship("Entity", back_populates="contexts")
    source_ref: Mapped["SourceRef | None"] = relationship("SourceRef")


class EntityRelation(Base):
    __tablename__ = "entity_relation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    from_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("entity.id"), nullable=False, index=True
    )
    to_entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("entity.id"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    project_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("project.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())

    from_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[from_entity_id], back_populates="outgoing_relations"
    )
    to_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[to_entity_id], back_populates="incoming_relations"
    )


class EntityMetadata(Base):
    __tablename__ = "entity_metadata"
    __table_args__ = (UniqueConstraint("entity_id", "meta_type", name="uq_entity_metadata_type"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("entity.id"), nullable=False)
    meta_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime(), server_default=func.now(), onupdate=func.now()
    )

    entity: Mapped["Entity"] = relationship("Entity", back_populates="metadata_entries")


class EntityHistory(Base):
    __tablename__ = "entity_history"
    __table_args__ = (UniqueConstraint("entity_id", "revision_no", name="uq_entity_history_rev"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("entity.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_fields: Mapped[dict | None] = mapped_column(JSON)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now(), index=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="history")


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    project_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scope: Mapped[str] = mapped_column(String(10), nullable=False, default="read")  # read | write
    expires_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())


class EntityAuditLog(Base):
    __tablename__ = "entity_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    before_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now(), index=True)


class SourceRef(Base):
    __tablename__ = "source_ref"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    uri: Mapped[str] = mapped_column(String(2000), nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    version: Mapped[str | None] = mapped_column(String(100))
    retrieved_at: Mapped[datetime | None] = mapped_column(UtcDateTime())
    created_at: Mapped[datetime] = mapped_column(UtcDateTime(), server_default=func.now())
