from sqlalchemy import Column, ForeignKey, UUID, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from .dbconf import Base

class Users(Base):
    __tablename__ = "users"

    user_uuid = Column(UUID, primary_key=True)
    user_fname = Column(String, nullable=False)
    user_lname = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    user_password = Column(String, nullable=False)

    sprite_instances = relationship("SpriteInstances", back_populates="user")
    tasks = relationship("Tasks", back_populates="user")
    forums = relationship(secondary="ForumMembers", back_populates="users")
    user_logs = relationship("UserLogs", back_populates="user")

class Sprites(Base):
    __tablename__ = "sprites"

    sprite_uuid = Column(UUID, primary_key=True)
    sprite_sources = Column(String, nullable=False, unique=True)
    sprite_summon_chance = Column(Float, nullable=False)

class Forums(Base):
    __tablename__ = "forums"

    forum_uuid = Column(UUID, primary_key=True)
    forum_title = Column(String, nullable=False, unique=True)
    forum_status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    forum_members = relationship("ForumMembers", back_populates="forum")
    forum_comments = relationship("ForumComments", back_populates="forum")
    users = relationship(secondary="Users", back_populates="forums")

class Tasks(Base):
    __tablename__ = "tasks"

    task_uuid = Column(UUID, primary_key=True)
    task_details = Column(String, nullable=False)
    task_deadline = Column(DateTime, nullable=False)
    user_uuid = Column(UUID, ForeignKey("user.user_uuid"), nullable=False)

    user = relationship("Users", back_populates="tasks")
    task_logs = relationship("TaskLogs", back_populates="task")

class SpriteInstances(Base):
    __tablename__ = "sprite_instances"

    sprite_instance_uuid = Column(UUID, primary_key=True)
    acquisition_date = Column(DateTime, nullable=False)
    sprite_uuid = Column(UUID, ForeignKey("sprites.sprite_uuid"), nullable=False)
    user_uuid = Column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    user = relationship("Users", back_populates="sprite_instances")
    sprite_instance_logs = relationship("SpriteInstanceLogs", back_populates="sprite_instance")

class ForumMembers(Base):
    __tablename__ = "forum_members"

    forum_member_uuid = Column(UUID, primary_key=True)
    is_owner = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    forum_uuid = Column(UUID, ForeignKey("forums.forum_uuid"), nullable=False)
    user_uuid = Column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    forum = relationship("Forums", back_populates="forum_members")

class ForumComments(Base):
    __tablename__ = "forum_comments"

    forum_comment_uuid = Column(UUID, primary_key=True)
    forum_comment = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    forum_uuid = Column(UUID, ForeignKey("forums.forum_uuid"), nullable=False)
    forum_member_uuid = Column(UUID, ForeignKey("forum_members.forum_member_uuid"), nullable=False)

    forum = relationship("Forums", back_populates="forum_comments")

class TaskLogs(Base):
    __tablename__ = "task_logs"

    task_log_uuid = Column(UUID, primary_key=True)
    task_details = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    task_uuid = Column(UUID, ForeignKey("tasks.task_uuid"), nullable=False)

    task = relationship("Tasks", back_populates="task_logs")

class UserLogs(Base):
    __tablename__ = "user_logs"

    user_log_uuid = Column(UUID, primary_key=True)
    user_details = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    user_uuid = Column(UUID, ForeignKey("users.user_uuid"), nullable=False)

    user = relationship("Users", back_populates="user_logs")

class SpriteInstanceLogs(Base):
    __tablename__ = "sprite_logs"

    sprite_log_uuid = Column(UUID, primary_key=True)
    sprite_log_details = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    sprite_instance_uuid = Column(UUID, ForeignKey("sprite_instances.sprite_instance_uuid"), nullable=False)

    sprite_instance = relationship("SpriteInstances", back_populates="sprite_instances_logs")
