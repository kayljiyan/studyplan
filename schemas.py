from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime

class TokenData(BaseModel):
    user_uuid: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    token_type: str | None = None

class ForumCommentAddToDB(BaseModel):
    forum_comment: str
    forum_uuid: UUID4
    user_uuid: UUID4
class ForumComments(ForumCommentAddToDB):
    forum_comment_uuid: UUID4
    created_at: datetime
    class Config:
        from_attributes = True

class ForumMemberAddToDB(BaseModel):
    is_owner: bool
    user_name: str
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
    user_points: int
    sprite_instances: list[SpriteInstances]
    tasks: list[Tasks]
    class Config:
        from_attributes = True

class ForumAddToDB(BaseModel):
    forum_title: str
    forum_category: str
    forum_details: str
    forum_status: str

class Forums(ForumAddToDB):
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
