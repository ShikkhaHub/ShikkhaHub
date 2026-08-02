"""Community models: discussion posts, tags, communities and votes.

The Q&A system (`qa.py`) covers structured questions/answers; this module adds
free-form community discussion, topic tagging and interest-based communities.
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


class Community(Base):
    """An interest-based community (e.g. medical_admission, engineering, madrasah)."""

    __tablename__ = "communities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    name_bn = Column(String(200), nullable=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    icon = Column(String(100), nullable=True)
    member_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("DiscussionPost", back_populates="community")
    members = relationship("CommunityMember", back_populates="community")

    def __repr__(self) -> str:
        return f"<Community {self.name}>"


class Tag(Base):
    """A topical tag applied to discussion posts."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)
    post_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    post_tags = relationship("PostTag", back_populates="tag")

    __table_args__ = (Index("idx_tag_category", "category"),)

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class DiscussionPost(Base):
    """A free-form community discussion post."""

    __tablename__ = "discussion_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    community_id = Column(
        Integer, ForeignKey("communities.id"), nullable=True, index=True
    )
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=True, index=True
    )
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(
        String(50), default="discussion"
    )  # discussion, question, news, help, review_post
    status = Column(
        String(20), default="published"
    )  # published, hidden, flagged, removed, draft
    is_pinned = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="discussion_posts")
    community = relationship("Community", back_populates="posts")
    institution = relationship("Institution")
    votes = relationship(
        "PostVote", back_populates="post", cascade="all, delete-orphan"
    )
    tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_post_status_time", "status", "created_at"),
        Index("idx_post_community", "community_id", "created_at"),
        Index("idx_post_user", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<DiscussionPost {self.id} {self.title!r}>"


class PostVote(Base):
    """Up/down vote on a discussion post (one per user per post)."""

    __tablename__ = "post_votes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_upvote = Column(Boolean, nullable=False)  # True = up, False = down
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("DiscussionPost", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_vote_user"),
        Index("idx_post_vote_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<PostVote post={self.post_id} user={self.user_id} up={self.is_upvote}>"


class PostTag(Base):
    """Many-to-many join between discussion posts and tags."""

    __tablename__ = "post_tags"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("discussion_posts.id"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("DiscussionPost", back_populates="tags")
    tag = relationship("Tag", back_populates="post_tags")

    __table_args__ = (
        UniqueConstraint("post_id", "tag_id", name="uq_post_tag"),
        Index("idx_post_tag_tag", "tag_id"),
    )

    def __repr__(self) -> str:
        return f"<PostTag post={self.post_id} tag={self.tag_id}>"


class CommunityMember(Base):
    """A user's membership in a community (with an optional role)."""

    __tablename__ = "community_members"

    id = Column(Integer, primary_key=True, index=True)
    community_id = Column(
        Integer, ForeignKey("communities.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    member_role = Column(String(50), default="member")  # member, moderator, admin
    joined_at = Column(DateTime, default=datetime.utcnow)

    community = relationship("Community", back_populates="members")

    __table_args__ = (
        UniqueConstraint(
            "community_id", "user_id", name="uq_community_member"
        ),
    )

    def __repr__(self) -> str:
        return f"<CommunityMember community={self.community_id} user={self.user_id}>"
