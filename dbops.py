from sqlalchemy.orm import Session
import models, schemas, security

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
    user = db.query(models.Users).filter(models.Users.user_email == user_email)
    if user:
        user.update({'is_confirmed': True})
        db.commit()
