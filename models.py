from datetime import date
from typing import List

from sqlalchemy import (
    DATE,
    UUID,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

import security as security
from dbconf import Base


class Sprite(Base):
    __tablename__ = "sprites"

    sprite_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
    sprite_source = Column(String, nullable=False, unique=True)
    sprite_summon_chance = Column(Float, nullable=False)

    sprite_instances: Mapped[List["SpriteInstance"]] = relationship(
        back_populates="sprite"
    )


class Forum(Base):
    __tablename__ = "forums"

    forum_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
    forum_title = Column(String, nullable=False)
    forum_category = Column(String, nullable=False)
    forum_details = Column(String, nullable=False)
    forum_status = Column(String, nullable=False)
    created_at = Column(Date, nullable=True, default=security.get_locale_datetime())

    forum_members: Mapped[List["ForumMember"]] = relationship(back_populates="forum")
    forum_comments: Mapped[List["ForumComment"]] = relationship(
        "ForumComment", back_populates="forum"
    )


class User(Base):
    __tablename__ = "users"

    user_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
    user_fname = Column(String, nullable=False)
    user_lname = Column(String, nullable=False)
    user_email = Column(String, nullable=False, unique=True)
    user_password = Column(String, nullable=False)
    is_premium = Column(Boolean, nullable=False, default=False)
    is_confirmed = Column(Boolean, nullable=False, default=False)
    user_points = Column(Integer, nullable=False, default=0)
    push_notif = Column(Boolean, nullable=False, default=False)
    user_avatar = Column(String, nullable=False)
    created_at = Column(DATE, nullable=False, default=date.today())
    last_login = Column(DATE, nullable=False, default=date.today())

    sprite_instances: Mapped[List["SpriteInstance"]] = relationship(
        back_populates="user"
    )
    tasks: Mapped[List["Task"]] = relationship(back_populates="user")
    forum_comments: Mapped[List["ForumComment"]] = relationship(back_populates="user")
    forum_members: Mapped[List["ForumMember"]] = relationship(back_populates="user")


class Task(Base):
    __tablename__ = "tasks"

    task_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
    task_details = Column(String, nullable=False)
    task_priority = Column(String, nullable=False)
    task_category = Column(String, nullable=False)
    task_deadline = Column(Date, nullable=False)
    task_time = Column(Time, nullable=False)
    is_done = Column(Boolean, default=False, nullable=False)
    user_uuid = mapped_column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tasks")
    # task_logs: Mapped[List["TaskLog"]] = relationship(back_populates="task")


class SpriteInstance(Base):
    __tablename__ = "sprite_instances"

    sprite_instance_uuid = mapped_column(
        UUID, primary_key=True, default=security.generate_uuid
    )
    acquisition_date = Column(
        Date, nullable=False, default=security.get_locale_datetime
    )
    sprite_uuid = mapped_column(UUID, ForeignKey("sprites.sprite_uuid"), nullable=False)
    user_uuid = mapped_column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="sprite_instances")
    sprite: Mapped["Sprite"] = relationship(back_populates="sprite_instances")
    # sprite_instance_logs: Mapped[List["SpriteInstanceLog"]] = relationship(back_populates="sprite_instance")


class ForumMember(Base):
    __tablename__ = "forum_members"

    forum_member_uuid = mapped_column(
        UUID, primary_key=True, default=security.generate_uuid
    )
    user_name = Column(String, nullable=False)
    is_owner = Column(Boolean, nullable=False)
    created_at = Column(Date, nullable=True, default=security.get_locale_datetime())
    forum_uuid = mapped_column(UUID, ForeignKey("forums.forum_uuid"), nullable=False)
    user_uuid = mapped_column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    forum: Mapped["Forum"] = relationship(back_populates="forum_members")
    user: Mapped["User"] = relationship(back_populates="forum_members")


class ForumComment(Base):
    __tablename__ = "forum_comments"

    forum_comment_uuid = mapped_column(
        UUID, primary_key=True, default=security.generate_uuid
    )
    forum_comment = Column(String, nullable=False)
    created_at = Column(Date, nullable=False, default=security.get_locale_datetime())
    forum_uuid = mapped_column(UUID, ForeignKey("forums.forum_uuid"), nullable=False)
    user_uuid = mapped_column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    forum: Mapped["Forum"] = relationship(back_populates="forum_comments")
    user: Mapped["User"] = relationship(back_populates="forum_comments")


# class TaskLog(Base):
#     __tablename__ = "task_logs"

#     task_log_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
#     task_log_details = Column(String, nullable=False)
#     created_at = Column(Date, nullable=False)
#     task_uuid = mapped_column(UUID, ForeignKey("tasks.task_uuid"), nullable=False)

#     task: Mapped["Task"] = relationship(back_populates="task_logs")


class UserLog(Base):
    __tablename__ = "user_logs"

    user_log_uuid = mapped_column(
        UUID, primary_key=True, default=security.generate_uuid
    )
    user_log_details = Column(String, nullable=False)
    created_at = Column(Date, nullable=False, default=date.today())
    user_uuid = mapped_column(UUID, ForeignKey("users.user_uuid"), nullable=False)


# class SpriteInstanceLog(Base):
#     __tablename__ = "sprite_logs"

#     sprite_log_uuid = mapped_column(UUID, primary_key=True, default=security.generate_uuid)
#     sprite_log_details = Column(String, nullable=False)
#     created_at = Column(Date, nullable=False)
#     sprite_instance_uuid = mapped_column(UUID, ForeignKey("sprite_instances.sprite_instance_uuid"), nullable=False)

#     sprite_instance: Mapped["SpriteInstance"] = relationship(back_populates="sprite_instance_logs")
