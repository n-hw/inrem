from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deceased = Column(Boolean, default=False)

    # PIPA / 잊혀질 권리: 사용자가 계정 삭제를 요청한 시각.
    # PRD §6 NFR: 사용자 삭제 요청 시 30일 grace → 영구 삭제.
    # 이 컬럼이 NULL 이 아니면 계정은 "deletion pending" 상태.
    deletion_requested_at = Column(DateTime, nullable=True, default=None)

    # 온보딩 완료 시각. NULL 이면 신규 사용자 → 앱이 온보딩 화면으로 라우팅.
    onboarding_completed_at = Column(DateTime, nullable=True, default=None)

    # Push notifications
    fcm_token = Column(String, nullable=True)  # Firebase Cloud Messaging token

    # Guardian Pulse: Last activity tracking
    last_active_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    
    # ──────────────────────────────────────────────────────────────────
    # Cascade policy (PRD §6 — 잊혀질 권리)
    # Owner-side relationships use `cascade="all, delete-orphan"` so that
    # `db.delete(user)` issues child DELETEs through the ORM, regardless
    # of whether the DB FK has ON DELETE CASCADE. This is what
    # `account_service.purge_expired_deletions()` relies on.
    #
    # 잔여: `Asset.designated_executor_id` 와 `PulseEvent.resolved_by`
    # 는 *다른* 사용자를 가리킬 수 있다. 해당 다른 사용자가 삭제될 때
    # 이 컬럼들이 dangling 이 되므로, 출시 전 alembic 마이그레이션에서
    # `ondelete="SET NULL"` 로 바꿔야 한다 (TODO).
    # ──────────────────────────────────────────────────────────────────

    activity_signals = relationship(
        "ActivitySignal",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
    monitoring_policy = relationship(
        "MonitoringPolicy",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    pulse_events = relationship(
        "PulseEvent",
        foreign_keys="PulseEvent.user_id",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Guardian 매핑: 본인이 ward 인 행과 guardian 인 행 모두 함께 삭제.
    guardians = relationship(
        "Guardian",
        foreign_keys="Guardian.ward_id",
        back_populates="ward",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    wards = relationship(
        "Guardian",
        foreign_keys="Guardian.guardian_id",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # Timer (Task 22)
    config = relationship(
        "UserConfig",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    timer_status = relationship(
        "TimerStatus",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Heritage Box 자산 — 본인 소유. designated_executor_id 의 다른 사용자
    # 참조는 위 잔여 항목 참조.
    assets = relationship(
        "Asset",
        foreign_keys="Asset.user_id",
        cascade="all, delete-orphan",
    )

    # Life Narrator 기록.
    records = relationship(
        "Record",
        foreign_keys="Record.user_id",
        cascade="all, delete-orphan",
    )
