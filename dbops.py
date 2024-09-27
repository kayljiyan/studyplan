from sqlalchemy.orm import Session
from uuid import UUID
import models as models, schemas as schemas, security as security

def login(db: Session, username: str, password: str):
    password = security.hash_password(password)
    user = db.query(models.Users).where(models.Users.user_email == username and models.Users.user_password == password).first()
    if user is None:
        raise PermissionError(f'Incorrect username or password')
    elif user.is_confirmed:
        return user
    else:
        raise PermissionError(f'Email is not confirmed')

def register(db: Session, user: schemas.UserRegister):
    hashed_password = security.hash_password(user.user_password)
    db_user = models.Users(user_email=user.user_email, user_password=hashed_password, user_fname=user.user_fname, user_lname=user.user_lname)
    db.add(db_user)
    db.commit()

def confirm_email(db: Session, user_email: str):
    db_user = db.query(models.Users).filter(models.Users.user_email == user_email)
    if db_user:
        db_user.update({'is_confirmed': True})
        db.commit()

def create_task(db: Session, task: schemas.TaskAddToDB):
    db_task = models.Tasks(task_details=task.task_details, task_deadline=task.task_deadline, user_uuid=task.user_uuid)
    db.add(db_task)
    db.commit()

def update_task(db: Session, task: schemas.TaskUpdateToDB):
    db_task = db.query(models.Tasks).filter(models.Tasks.task_uuid == task.task_uuid)
    if db_task:
        db_task.update({
            'task_details': task.task_details,
            'task_deadline': task.task_deadline
        })
        db.commit()

def complete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = db.query(models.Tasks).filter(models.Tasks.task_uuid == task_uuid and models.Tasks.user_uuid == user_uuid)
    if db_task:
        db_task.update({
            'is_done': True
        })
        db.commit()

def delete_task(db: Session, task_uuid: UUID, user_uuid: UUID):
    db_task = db.query(models.Tasks).filter(models.Tasks.task_uuid == task_uuid and models.Tasks.user_uuid == user_uuid)
    if db_task:
        db_task.delete()
        db.commit()

def get_tasks(db: Session, user_uuid: UUID):
    tasks = db.query(models.Tasks).filter(models.Tasks.user_uuid == UUID(user_uuid)).all()
    return tasks
