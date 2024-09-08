from sqlalchemy.orm import Session
import models

def login(db: Session, username: str, password: str):
    return db.query(models.Users).where(models.Users.user_email == username and models.Users.user_password == password).first()
