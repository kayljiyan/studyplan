from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime

class TokenData(BaseModel):
    user_uuid: str | None = None
    user_email: str | None = None

class SpriteInstanceLogs(BaseModel):
    sprite_log_uuid: UUID4
    sprite_log_details: str
    created_at: datetime
    sprite_instance_uuid: UUID4

    class Config:
        orm_mode = True

class UserLogs(BaseModel):
    user_log_uuid: UUID4
    user_log_details: str
    created_at: datetime
    user_uuid: UUID4

    class Config:
        orm_mode = True

class TaskLogs(BaseModel):
    task_log_uuid: UUID4
    task_log_details: str
    created_at: datetime
    task_uuid: UUID4

    class Config:
        orm_mode = True

class ForumComments(BaseModel):
    forum_comment_uuid: UUID4
    forum_comment: str
    created_at: datetime
    forum_uuid: UUID4
    forum_member_uuid: UUID4

    class Config:
        orm_mode = True

class ForumMembers(BaseModel):
    forum_member_uuid: UUID4
    is_owner: bool
    created_at: datetime
    forum_uuid: UUID4
    user_uuid: UUID4

    class Config:
        orm_mode = True

class SpriteInstances(BaseModel):
    sprite_instance_uuid: UUID4
    acquisition_date: datetime
    sprite_uuid: UUID4
    user_uuid: UUID4
    sprite_instance_logs: list[SpriteInstanceLogs]

    class Config:
        orm_mode = True

class Tasks(BaseModel):
    task_uuid: UUID4
    task_details: str
    task_deadline: datetime
    user_uuid: UUID4
    task_logs: list[TaskLogs]

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    user_uuid: UUID4
    user_fname: str
    user_lname: str
    user_email: EmailStr
    user_password: str
    sprite_instances: list[SpriteInstances]
    tasks: list[Tasks]
    user_logs: list[UserLogs]

class Forums(BaseModel):
    forum_uuid: UUID4
    forum_title: str
    forum_status: str
    created_at: datetime
    forum_members: list[ForumMembers]
    forum_comments: list[ForumComments]
    users: list[UserBase]

    class Config:
        orm_mode = True

class Users(UserBase):
    forums: list[Forums]

    class Config:
        orm_mode = True

class Sprites(BaseModel):
    sprite_uuid: UUID4
    sprite_sources: str
    sprite_summon_chance: float

    class Config:
        orm_mode = True
