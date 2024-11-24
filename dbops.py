from uuid import UUID

from sqlalchemy.orm import Session, joinedload, load_only

import models as models
import schemas as schemas
import security as security


def login(db: Session, username: str, password: str):
    password = security.hash_password(password)
    user = (
        db.query(models.User)
        .filter(models.User.user_email == username)
        .filter(models.User.user_password == password)
        .first()
    )
    if user is None:
        raise PermissionError(f"Incorrect username or password")
    elif user.is_confirmed:
        return user
    else:
        raise PermissionError(f"Email is not confirmed")


def register(db: Session, user: schemas.UserRegister):
    hashed_password = security.hash_password(user.user_password)
    db_user = models.User(
        user_email=user.user_email,
        user_password=hashed_password,
        user_fname=user.user_fname,
        user_lname=user.user_lname,
    )
    db.add(db_user)
    db.commit()


def confirm_email(db: Session, user_email: str):
    db_user = db.query(models.User).filter(models.User.user_email == user_email)
    if db_user:
        db_user.update({"is_confirmed": True})
        db.commit()


def change_password(db: Session, user_uuid: UUID, old_password: str, new_password: str):
    old_password = security.hash_password(old_password)
    new_password = security.hash_password(new_password)
    db_user = (
        db.query(models.User)
        .filter(models.User.user_uuid == user_uuid)
        .filter(models.User.user_password == old_password)
        .first()
    )
    db_user.user_password = new_password
    db.commit()


def recover_password(db: Session, user_email: str, new_password: str):
    new_password = security.hash_password(new_password)
    db_user = db.query(models.User).filter(models.User.user_email == user_email).first()
    if db_user:
        db_user.user_password = new_password
        db.commit()
    else:
        raise PermissionError("User not found")


def toggle_push(db: Session, user_uuid: UUID, toggle: bool):
    db_user = db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
    print(toggle)
    db_user.push_notif = toggle
    db.commit()


def get_points(db: Session):
    db_user = db.query(models.User.user_uuid, models.User.user_points).all()
    results = [
        {"user_uuid": user_uuid, "user_points": user_points}
        for user_uuid, user_points in db_user
    ]
    return results


def get_user(db: Session, user_uuid: UUID):
    db_user: models.User = (
        db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
    )
    if db_user:
        print(db_user)
        return db_user


def create_task(db: Session, task: schemas.TaskAddToDB):
    db_task = models.Task(
        task_details=task.task_details,
        task_category=task.task_category,
        task_priority=task.task_priority,
        task_deadline=task.task_deadline,
        user_uuid=task.user_uuid,
    )
    db.add(db_task)
    db.commit()


def update_task(db: Session, task: schemas.TaskUpdateToDB):
    db_task = (
        db.query(models.Task)
        .filter(models.Task.task_uuid == task.task_uuid)
        .filter(models.Task.user_uuid == task.user_uuid)
    )
    if db_task:
        db_task.update(
            {
                "task_details": task.task_details,
                "task_priority": task.task_priority,
                "task_category": task.task_category,
                "task_deadline": task.task_deadline,
            }
        )
        db.commit()


def complete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = (
        db.query(models.Task)
        .filter(models.Task.task_uuid == task_uuid)
        .filter(models.Task.user_uuid == user_uuid)
        .first()
    )
    if db_task:
        db_task.is_done = True
        task_priority = db_task.task_priority
        print(task_priority)
        db.commit()
        db_user = (
            db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
        )
        if db_user:
            match (task_priority):
                case "High":
                    db_user.user_points += 5
                case "Normal":
                    db_user.user_points += 3
                case "Low":
                    db_user.user_points += 1
            db.commit()


def complete_session(db: Session, user_uuid: UUID):
    db_user = db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
    if db_user:
        db_user.user_points += 5
        db.commit()


def delete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = (
        db.query(models.Task)
        .filter(models.Task.task_uuid == task_uuid)
        .filter(models.Task.user_uuid == user_uuid)
    )
    if db_task:
        db_task.delete()
        db.commit()


def get_tasks(db: Session, user_uuid: UUID):
    tasks = (
        db.query(models.Task)
        .filter(models.Task.user_uuid == UUID(user_uuid))
        .options(joinedload(models.Task.user))
        .all()
    )
    return tasks


def create_forum(db: Session, forum: schemas.ForumAddToDB, forum_owner: dict):
    db_forum = models.Forum(
        forum_title=forum.forum_title,
        forum_category=forum.forum_category,
        forum_details=forum.forum_details,
        forum_status=forum.forum_status,
    )
    db.add(db_forum)
    db.commit()
    forum_owner["forum_uuid"] = db_forum.forum_uuid
    db_forum_member = schemas.ForumMemberAddToDB(**forum_owner)
    db_forum_member = models.ForumMember(
        is_owner=db_forum_member.is_owner,
        user_name=db_forum_member.user_name,
        forum_uuid=db_forum_member.forum_uuid,
        user_uuid=db_forum_member.user_uuid,
    )
    db.add(db_forum_member)
    db.commit()


def create_comment(
    db: Session, comment: schemas.ForumCommentAddToDB, forum_member: dict
):
    db_comment = models.ForumComment(
        forum_comment=comment.forum_comment,
        forum_uuid=comment.forum_uuid,
        user_uuid=comment.user_uuid,
    )
    db.add(db_comment)
    db.commit()
    forum_member["forum_uuid"] = db_comment.forum_uuid
    db_forum_member = schemas.ForumMemberAddToDB(**forum_member)
    members = len(
        db.query(models.ForumMember)
        .filter(models.ForumMember.forum_uuid == db_forum_member.forum_uuid)
        .filter(models.ForumMember.user_uuid == db_forum_member.user_uuid)
        .all()
    )
    if members == 0:
        db_forum_member = models.ForumMember(
            is_owner=db_forum_member.is_owner,
            user_name=db_forum_member.user_name,
            forum_uuid=db_forum_member.forum_uuid,
            user_uuid=db_forum_member.user_uuid,
        )
        db.add(db_forum_member)
        db.commit()


def get_forums(db: Session):
    forums = (
        db.query(models.Forum)
        .options(
            joinedload(models.Forum.forum_comments)
            .joinedload(models.ForumComment.user)
            .load_only(models.User.user_avatar),
            joinedload(models.Forum.forum_members)
            .joinedload(models.ForumMember.user)
            .load_only(models.User.user_avatar),
        )
        .all()
    )
    return forums


def get_forum(forum_uuid: UUID, db: Session):
    forum = (
        db.query(models.Forum)
        .filter(models.Forum.forum_uuid == UUID(forum_uuid))
        .options(
            joinedload(models.Forum.forum_comments)
            .joinedload(models.ForumComment.user)
            .load_only(models.User.user_avatar),
            joinedload(models.Forum.forum_members)
            .joinedload(models.ForumMember.user)
            .load_only(models.User.user_avatar),
        )
        .all()
    )
    return forum


def get_task(task_uuid: UUID, db: Session):
    task = db.query(models.Task).filter(models.Task.task_uuid == UUID(task_uuid)).all()
    return task


def gacha_life(db: Session, user_uuid: UUID, pull: int):
    from random import choices

    sources = []
    probabilities = []
    sprites = db.query(models.Sprite).all()
    for sprite in sprites:
        sources.append({str(sprite.sprite_uuid): sprite.sprite_source})
        probabilities.append(sprite.sprite_summon_chance)
    choice: dict = choices(sources, probabilities, k=pull)
    print(choice)
    for element in choice:
        print(list(element.keys())[0])
        db_sprite_instance = models.SpriteInstance(
            user_uuid=user_uuid, sprite_uuid=list(element.keys())[0]
        )
        db.add(db_sprite_instance)
        db.commit()
    db_user = db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
    db_user.user_points -= pull * 20
    db.commit()


def get_sprites(db: Session, user_uuid: UUID):
    sprites = (
        db.query(models.SpriteInstance)
        .filter(models.SpriteInstance.user_uuid == UUID(user_uuid))
        .options(joinedload(models.SpriteInstance.sprite))
        .all()
    )
    return sprites


def change_avatar(db: Session, user_uuid: UUID, avatar: str):
    db_user = db.query(models.User).filter(models.User.user_uuid == user_uuid).first()
    db_user.user_avatar = avatar
    db.commit()


# def get_user(db: Session, user_uuid: UUID):
#     db_user = db.query(models.User.push_notif, models.User.user_avatar).filter(models.User.user_uuid == UUID(user_uuid)).all()
#     results = [{"user_uuid": user_uuid, "push_notif": push_notif, "user_avatar": user_avatar} for push_notif, user_avatar in db_user]
#     return results
