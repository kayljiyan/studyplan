from datetime import timedelta
from typing import Annotated, List

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import consts as consts
import dbops as dbops
import models as models
import schemas as schemas
import security as security
from dbconf import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://studyplan-one.vercel.app", "https://studyplan.fun"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/login")
async def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        account = dbops.login(db, request.username, request.password)
        data = {
            "user_uuid": str(account.user_uuid),
            "user_email": account.user_email,
            "user_name": f"{account.user_fname} {account.user_lname}",
            "push_notif": account.push_notif,
            "user_avatar": account.user_avatar,
            "token_type": "access",
        }
        refresh_token_expiry_date = timedelta(days=consts.REFRESH_TOKEN_EXPIRE_DAYS)
        access_token_expiry_date = timedelta(hours=consts.ACCESS_TOKEN_EXPIRE_HOURS)
        refresh_token = security.generate_refresh_token(refresh_token_expiry_date)
        access_token = security.generate_access_token(data, access_token_expiry_date)
        response.status_code = status.HTTP_200_OK
        response.set_cookie(
            key="REFRESH_TOKEN",
            value=refresh_token,
            httponly=True,
            samesite="none",
            secure=True,
        )
        log = {
            "user_log_details": "LOGGED IN",
            "user_uuid": account.user_uuid
        }
        log = schemas.UserLogs(**log)
        dbops.add_log(db, log)
        return {"access_token": access_token, "access_type": "Bearer"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["WWW-Authenticate"] = "Bearer"
        return {"detail": str(e)}


@app.post("/api/v1/register")
async def register(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        user = schemas.UserRegister(**data)
        dbops.register(db, user)
        SUBJECT = "Email Confirmation"
        TEXT = f"""
        Your email is awaiting confirmation by the admin.
        """
        security.send_email(user.user_email, SUBJECT, TEXT)
        response.status_code = status.HTTP_201_CREATED
        return {"detail": "Please check your email for confirmation link"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/forgot")
async def forgot_password(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        user_email = data.get("user_email")
        SUBJECT = "Password Recovery"
        TEXT = f"""
        Recover your password with the link below.

        https://studyplan-one.vercel.app/recover/{user_email}"""
        security.send_email(user_email, SUBJECT, TEXT)
        response.status_code = status.HTTP_201_CREATED
        return {"detail": "Please check your email for confirmation link"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/user")
async def get_user(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        user: models.User = dbops.get_user(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return {"data": payload, "user_avatar": user.user_avatar}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/users")
async def get_users(
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        users: List[models.User] = dbops.get_users(db)
        response.status_code = status.HTTP_200_OK
        return {"data": users}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/confirm/{user_email}")
async def confirm_email(
    response: Response,
    user_email: str,
    db: Session = Depends(get_db),
):
    try:
        dbops.confirm_email(db, user_email)
        SUBJECT = "Email Confirmation"
        TEXT = f"""
        Your email has been confirmed. Please proceed to login.

        https://studyplan-one.vercel.app/"""
        security.send_email(user_email, SUBJECT, TEXT)
        response.status_code = status.HTTP_202_ACCEPTED
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/disable/{user_email}")
async def disable_user(
    response: Response,
    user_email: str,
    db: Session = Depends(get_db),
):
    try:
        dbops.disable_user(db, user_email)
        SUBJECT = "Account Disabled"
        TEXT = f"""
        Your email has been disabled by the admin."""
        security.send_email(user_email, SUBJECT, TEXT)
        response.status_code = status.HTTP_202_ACCEPTED
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/password")
async def change_password(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.change_password(
            db, payload.user_uuid, data.get("old_password"), data.get("new_password")
        )
        response.status_code = status.HTTP_200_OK
        return {"detail": "Password has been changed", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/recover")
async def recover_password(
    request: Request, response: Response, db: Session = Depends(get_db)
):
    try:
        data = await request.json()
        dbops.recover_password(db, data.get("user_email"), data.get("new_password"))
        response.status_code = status.HTTP_200_OK
        return {"detail": "Password has been changed"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/push")
async def toggle_push(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.toggle_push(db, payload.user_uuid, data.get("push_notif"))
        response.status_code = status.HTTP_200_OK
        return {"detail": "Push notification toggled", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/points")
async def get_points(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        users = dbops.get_points(db)
        response.status_code = status.HTTP_200_OK
        return {"data": users, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/sprites")
async def get_sprites(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        sprites = dbops.get_sprites(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return {"data": sprites, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/sprites/single")
async def single_pull(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.gacha_life(db, payload.user_uuid, 1)
        response.status_code = status.HTTP_200_OK
        return {"detail": "Single pull successful", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/sprites/ten")
async def ten_pull(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.gacha_life(db, payload.user_uuid, 10)
        response.status_code = status.HTTP_200_OK
        return {"detail": "Ten pull successful", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/avatar")
async def change_avatar(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        data = await request.json()
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.change_avatar(db, payload.user_uuid, data.get("user_avatar"))
        response.status_code = status.HTTP_200_OK
        return {"detail": "Avatar changed", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/task")
async def create_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        data = await request.json()
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        print(payload)
        data = {**data, "user_uuid": payload.user_uuid}
        task = schemas.TaskAddToDB(**data)
        dbops.create_task(db, task)
        response.status_code = status.HTTP_201_CREATED
        return {"detail": "Task has been created", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/task")
async def update_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        data = await request.json()
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        data = {**data, "user_uuid": payload.user_uuid}
        task = schemas.TaskUpdateToDB(**data)
        dbops.update_task(db, task)
        response.status_code = status.HTTP_202_ACCEPTED
        return {"detail": "Task has been updated", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/task/{task_uuid}")
async def complete_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.complete_task(db, task_uuid, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return {"detail": "Task has been completed", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.patch("/api/v1/session")
async def complete_session(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.complete_session(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return {"detail": "Session has been completed", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.delete("/api/v1/task/{task_uuid}")
async def delete_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        dbops.delete_task(db, task_uuid, payload.user_uuid)
        response.status_code = (
            status.HTTP_204_NO_CONTENT
            if access_token is not None
            else status.HTTP_202_ACCEPTED
        )
        return {"detail": "Task has been deleted", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/tasks")
async def get_tasks(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        tasks = dbops.get_tasks(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return {"data": tasks, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/task/{task_uuid}")
async def get_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    task_uuid: str,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        tasks = dbops.get_task(task_uuid, db)
        response.status_code = status.HTTP_200_OK
        return {"data": tasks, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/forum")
async def create_forum(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        data = await request.json()
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        forum_owner = {
            "is_owner": True,
            "user_uuid": payload.user_uuid,
            "user_name": payload.user_name,
        }
        forum = schemas.ForumAddToDB(**data)
        dbops.create_forum(db, forum, forum_owner)
        log = {
            "user_log_details": "FORUM POSTED",
            "user_uuid": payload.user_uuid
        }
        log = schemas.UserLogs(**log)
        dbops.add_log(db, log)
        response.status_code = status.HTTP_201_CREATED
        return {"detail": "Forum has been created", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.post("/api/v1/comment")
async def create_comment(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        data = await request.json()
        print(access_token)
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        data["user_uuid"] = payload.user_uuid
        forum_member = {
            "is_owner": False,
            "user_uuid": payload.user_uuid,
            "user_name": payload.user_name,
        }
        comment = schemas.ForumCommentAddToDB(**data)
        dbops.create_comment(db, comment, forum_member)
        log = {
            "user_log_details": "COMMENT POSTED",
            "user_uuid": payload.user_uuid
        }
        log = schemas.UserLogs(**log)
        dbops.add_log(db, log)
        response.status_code = status.HTTP_201_CREATED
        return {"detail": "Comment has been submitted", "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/forums")
async def get_forums(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        forums = dbops.get_forums(db)
        response.status_code = status.HTTP_200_OK
        return {"data": forums, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/{user_id}/forums")
async def get_user_forums(
    response: Response,
    user_id: str,
    db: Session = Depends(get_db),
):
    try:
        forums = dbops.get_user_forums(db, user_id)
        response.status_code = status.HTTP_200_OK
        return {"data": forums}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

@app.get("/api/v1/logs")
async def get_logs(
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        forums = dbops.get_logs(db)
        response.status_code = status.HTTP_200_OK
        return {"data": forums}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}

@app.delete("/api/v1/forums/{forum_id}")
async def delete_user_forum(
    response: Response,
    forum_id: str,
    db: Session = Depends(get_db),
):
    try:
        forums = dbops.delete_forum(db, forum_id)
        response.status_code = status.HTTP_200_OK
        return {"data": forums}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/{user_id}/comments")
async def get_user_comments(
    response: Response,
    user_id: str,
    db: Session = Depends(get_db),
):
    try:
        forums = dbops.get_user_comments(db, user_id)
        response.status_code = status.HTTP_200_OK
        return {"data": forums}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.delete("/api/v1/comment/{comment_id}")
async def delete_user_comment(
    response: Response,
    comment_id: str,
    db: Session = Depends(get_db),
):
    try:
        forums = dbops.delete_comment(db, comment_id)
        response.status_code = status.HTTP_200_OK
        return {"data": forums}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


@app.get("/api/v1/forum/{forum_uuid}")
async def get_forum(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    forum_uuid: str,
    db: Session = Depends(get_db),
):
    try:
        refresh_token = request.cookies.get("REFRESH_TOKEN")
        payload, access_token = security.verify_access_token(
            refresh_token, access_token
        )
        payload = schemas.TokenData(**payload)
        forums = dbops.get_forum(forum_uuid, db)
        response.status_code = status.HTTP_200_OK
        return {"data": forums, "access_token": access_token}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"detail": str(e)}


def main():
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run("main:app", port=8000, reload=True)


if __name__ == "__main__":
    main()
