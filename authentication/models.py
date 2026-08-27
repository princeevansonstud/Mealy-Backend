from __future__ import annotations

from datetime import datetime, timezone

from passlib.hash import bcrypt
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db import Base


class User(Base):
    """Application user mapped to the existing ``authentication_user`` table."""

    __tablename__ = "authentication_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    password: Mapped[str] = mapped_column(String(128), nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    outstanding_tokens: Mapped[list[OutstandingToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @classmethod
    def create(cls, email: str, password: str, **fields: object) -> "User":
        if not email:
            raise ValueError("Email is required")
        return cls(email=email.strip().lower(), password=bcrypt.hash(password), **fields)

    def set_password(self, raw_password: str) -> None:
        self.password = bcrypt.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.verify(raw_password, self.password)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_username(self) -> str:
        return self.email

    def __str__(self) -> str:
        return self.email


class OutstandingToken(Base):
    """SQLAlchemy mapping for the existing SimpleJWT token table."""

    __tablename__ = "token_blacklist_outstandingtoken"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    jti: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("authentication_user.id", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )

    user: Mapped[User | None] = relationship(back_populates="outstanding_tokens")
    blacklisted_token: Mapped[BlacklistedToken | None] = relationship(
        back_populates="token", uselist=False, cascade="all, delete-orphan"
    )


class BlacklistedToken(Base):
    __tablename__ = "token_blacklist_blacklistedtoken"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    token_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "token_blacklist_outstandingtoken.id", deferrable=True, initially="DEFERRED"
        ),
        nullable=False,
        unique=True,
    )

    token: Mapped[OutstandingToken] = relationship(back_populates="blacklisted_token")