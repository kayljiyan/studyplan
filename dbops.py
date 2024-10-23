from sqlalchemy.orm import Session, joinedload
from uuid import UUID
import models as models, schemas as schemas, security as security

def login(db: Session, username: str, password: str):
    password = security.hash_password(password)
    user = db.query(models.User).where(models.User.user_email == username and models.User.user_password == password).first()
    if user is None:
        raise PermissionError(f'Incorrect username or password')
    elif user.is_confirmed:
        return user
    else:
        raise PermissionError(f'Email is not confirmed')

def register(db: Session, user: schemas.UserRegister):
    hashed_password = security.hash_password(user.user_password)
    db_user = models.User(user_email=user.user_email, user_password=hashed_password, user_fname=user.user_fname, user_lname=user.user_lname)
    db.add(db_user)
    db.commit()

def confirm_email(db: Session, user_email: str):
    db_user = db.query(models.User).filter(models.User.user_email == user_email)
    if db_user:
        db_user.update({'is_confirmed': True})
        db.commit()

def create_task(db: Session, task: schemas.TaskAddToDB):
    db_task = models.Task(task_details=task.task_details, task_category=task.task_category, task_priority=task.task_priority, task_deadline=task.task_deadline, user_uuid=task.user_uuid)
    db.add(db_task)
    db.commit()

def update_task(db: Session, task: schemas.TaskUpdateToDB):
    db_task = db.query(models.Task).filter(models.Task.task_uuid == task.task_uuid, models.Task.user_uuid == task.user_uuid)
    if db_task:
        db_task.update({
            'task_details': task.task_details,
            'task_priority': task.task_priority,
            'task_category': task.task_category,
            'task_deadline': task.task_deadline,
            'is_done': task.is_done
        })
        db.commit()

def complete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = db.query(models.Task).filter(models.Task.task_uuid == task_uuid and models.Task.user_uuid == user_uuid)
    if db_task:
        db_task.update({
            'is_done': True
        })
        db.commit()

def delete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = db.query(models.Task).filter(models.Task.task_uuid == task_uuid and models.Task.user_uuid == user_uuid)
    if db_task:
        db_task.delete()
        db.commit()

def get_tasks(db: Session, user_uuid: UUID):
    tasks = db.query(models.Task).filter(models.Task.user_uuid == UUID(user_uuid)).options(joinedload(models.Task.user), joinedload(models.Task.task_logs)).all()
    return tasks

def create_forum(db: Session, forum: schemas.ForumAddToDB, forum_owner: dict):
    db_forum = models.Forum(
        forum_title=forum.forum_title,
        forum_status=forum.forum_status
    )
    db.add(db_forum)
    print(forum_owner)
    db.commit()
    print(forum_owner)
    forum_owner["forum_uuid"] = db_forum.forum_uuid
    print(forum_owner)
    db_forum_member = schemas.ForumMemberAddToDB(**forum_owner)
    db_forum_member = models.ForumMember(
        is_owner=db_forum_member.is_owner,
        user_name=db_forum_member.user_name,
        forum_uuid=db_forum_member.forum_uuid,
        user_uuid=db_forum_member.user_uuid
    )
    db.add(db_forum_member)
    db.commit()

def get_forums(db: Session):
    forums = db.query(models.Forum).options(joinedload(models.Forum.forum_comments), joinedload(models.Forum.forum_members)).all()
    return forums
