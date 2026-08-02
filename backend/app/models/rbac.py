"""Admin / RBAC models for ShikkhaHub platform governance.

A granular role-permission model over the existing `users` table. `AdminProfile`
links a user to admin capabilities; `Permission`/`RolePermission` provide
fine-grained access control; `AuditLog` keeps an immutable record of every
privileged action.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Role(Base):
    """Named collection of permissions (super_admin, editor, verifier, moderator)."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)  # system roles cannot be deleted
    created_at = Column(DateTime, default=datetime.utcnow)

    admins = relationship("AdminProfile", back_populates="role")
    permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


class Permission(Base):
    """A granular capability (e.g. institutions.update, institutions.verify)."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False)  # resource.action
    name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    role_permissions = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"


class RolePermission(Base):
    """Many-to-many join between roles and permissions."""

    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    permission_id = Column(
        Integer, ForeignKey("permissions.id"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    def __repr__(self) -> str:
        return f"<RolePermission role={self.role_id} perm={self.permission_id}>"


class AdminProfile(Base):
    """Admin record linking a user to a role and admin metadata."""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)
    department = Column(String(200), nullable=True)  # data, moderation, tech, ops
    title = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="admin_profile")
    role = relationship("Role", back_populates="admins")

    __table_args__ = (Index("idx_admin_role", "role_id"),)

    def __repr__(self) -> str:
        return f"<AdminProfile user={self.user_id} role={self.role_id}>"


class AuditLog(Base):
    """Immutable record of privileged actions across the platform."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    actor_role = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # institutions.update
    entity_type = Column(String(100), nullable=True, index=True)
    entity_id = Column(String(100), nullable=True)
    changes = Column(Text, nullable=True)  # JSON before/after
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    actor = relationship("User", foreign_keys=[actor_id])

    __table_args__ = (
        Index("idx_audit_action_time", "action", "created_at"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_actor", "actor_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} entity={self.entity_type}:{self.entity_id}>"
