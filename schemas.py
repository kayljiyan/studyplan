from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime

class TokenData(BaseModel):
    user_uuid: str | None = None
    user_email: str | None = None
    token_type: str | None = None

class SpriteInstanceLogs(BaseModel):
    sprite_log_uuid: UUID4
    sprite_log_details: str
    created_at: datetime
    sprite_instance_uuid: UUID4

    class Config:
        from_attributes = True

class UserLogs(BaseModel):
    user_log_uuid: UUID4
    user_log_details: str
    created_at: datetime
    user_uuid: UUID4

    class Config:
        from_attributes = True

class TaskLogs(BaseModel):
    task_log_uuid: UUID4
    task_log_details: str
    created_at: datetime
    task_uuid: UUID4

    class Config:
        from_attributes = True

class ForumCommentAddToDB(BaseModel):
    forum_comment: str
    created_at: datetime
    forum_uuid: UUID4
    user_uuid: UUID4
class ForumComments(ForumCommentAddToDB):
    forum_comment_uuid: UUID4
    class Config:
        from_attributes = True

class ForumMemberAddToDB(BaseModel):
    is_owner: bool
    forum_uuid: UUID4
    user_uuid: UUID4

class ForumMembers(ForumMemberAddToDB):
    forum_member_uuid: UUID4
    created_at: datetime
    class Config:
        from_attributes = True

class SpriteInstanceAddToDB(BaseModel):
    acquisition_date: datetime
    sprite_uuid: UUID4
    user_uuid: UUID4
class SpriteInstances(SpriteInstanceAddToDB):
    sprite_instance_uuid: UUID4
    sprite_instance_logs: list[SpriteInstanceLogs]
    class Config:
        from_attributes = True

class TaskAddToDB(BaseModel):
    task_details: str
    task_priority: str
    task_category: str
    task_deadline: datetime
    is_done: bool
    user_uuid: UUID4

class TaskUpdateToDB(TaskAddToDB):
    task_uuid: UUID4

class Tasks(TaskUpdateToDB):
    is_done: bool
    task_logs: list[TaskLogs]

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    user_email: EmailStr
    user_password: str

class UserRegister(UserLogin):
    user_fname: str
    user_lname: str

class Users(UserRegister):
    user_uuid: UUID4
    is_premium: bool
    is_confirmed: bool
    sprite_instances: list[SpriteInstances]
    tasks: list[Tasks]
    user_logs: list[UserLogs]
    class Config:
        from_attributes = True

class ForumAddToDB(BaseModel):
    forum_title: str
    forum_status: str
class Forums(BaseModel):
    forum_uuid: UUID4
    created_at: datetime
    forum_members: list[ForumMembers]
    forum_comments: list[ForumComments]
    class Config:
        from_attributes = True

class Sprites(BaseModel):
    sprite_uuid: UUID4
    sprite_sources: str
    sprite_summon_chance: float

    class Config:
        from_attributes = True
