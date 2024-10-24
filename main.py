from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from typing import Annotated
from datetime import timedelta
import models as models, schemas as schemas, dbops as dbops, security as security, consts as consts
from dbconf import SessionLocal, engine
from sqlalchemy.orm import Session

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
    allow_origins=["http://localhost:5173","https://studyplan-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/api/v1/login')
async def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        account = dbops.login(db,request.username,request.password)
        data = { "user_uuid": str(account.user_uuid), "user_email": account.user_email, "user_name": f"{account.user_fname} {account.user_lname}","token_type": "access" }
        refresh_token_expiry_date = timedelta(days=consts.REFRESH_TOKEN_EXPIRE_DAYS)
        access_token_expiry_date = timedelta(hours=consts.ACCESS_TOKEN_EXPIRE_HOURS)
        refresh_token = security.generate_refresh_token(refresh_token_expiry_date)
        access_token = security.generate_access_token(data, access_token_expiry_date)
        response.status_code = status.HTTP_200_OK
        response.set_cookie(key="REFRESH_TOKEN", value=refresh_token, httponly=True, samesite="none", secure=True)
        return {"access_token": access_token, "access_type": "Bearer"}
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        response.headers["WWW-Authenticate"] = "Bearer"
        return { "detail": str(e) }

@app.post('/api/v1/register')
async def register(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        data = await request.json()
        user = schemas.UserRegister(**data)
        dbops.register(db, user)
        security.send_email(user.user_email)
        response.status_code = status.HTTP_201_CREATED
        return { "detail": "Please check your email for confirmation link" }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/confirm/{user_email}')
async def confirm_email(
    response: Response,
    user_email: str,
    db: Session = Depends(get_db),
):
    try:
        dbops.confirm_email(db, user_email)
        response.status_code = status.HTTP_308_PERMANENT_REDIRECT
        return RedirectResponse("https://studyplan-frontend.vercel.app/")
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.post('/api/v1/task')
async def create_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        data = await request.json()
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        print(payload)
        data = {**data, 'user_uuid': payload.user_uuid}
        task = schemas.TaskAddToDB(**data)
        dbops.create_task(db, task)
        response.status_code = status.HTTP_201_CREATED
        return { "detail": "Task has been created", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.patch('/api/v1/task')
async def update_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        data = await request.json()
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        data = {**data, 'user_uuid': payload.user_uuid}
        task = schemas.TaskUpdateToDB(**data)
        dbops.update_task(db, task)
        response.status_code = status.HTTP_202_ACCEPTED
        return { "detail": "Task has been updated", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.patch('/api/v1/task/{task_uuid}')
async def complete_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        dbops.complete_task(db, task_uuid, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return { "detail": "Task has been completed", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.delete('/api/v1/task/{task_uuid}')
async def delete_task(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        dbops.delete_task(db, task_uuid, payload.user_uuid)
        response.status_code = status.HTTP_204_NO_CONTENT if access_token is not None else status.HTTP_202_ACCEPTED
        return { "detail": "Task has been deleted", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/tasks')
async def get_tasks(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        tasks = dbops.get_tasks(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return { "data": tasks, "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.post('/api/v1/forum')
async def create_forum(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        data = await request.json()
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        forum_owner = {
            "is_owner": True,
            "user_uuid": payload.user_uuid,
            "user_name": payload.user_name
        }
        forum = schemas.ForumAddToDB(**data)
        dbops.create_forum(db, forum, forum_owner)
        response.status_code = status.HTTP_201_CREATED
        return { "detail": "Forum has been created", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.post('/api/v1/comment')
async def create_comment(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        data = await request.json()
        print(access_token)
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        data["user_uuid"] = payload.user_uuid
        forum_member = {
            "is_owner": False,
            "user_uuid": payload.user_uuid,
            "user_name": payload.user_name
        }
        comment = schemas.ForumCommentAddToDB(**data)
        dbops.create_comment(db, comment, forum_member)
        response.status_code = status.HTTP_201_CREATED
        return { "detail": "Comment has been submitted", "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/forums')
async def get_forums(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        forums = dbops.get_forums(db)
        response.status_code = status.HTTP_200_OK
        return { "data": forums, "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/forum/{forum_uuid}')
async def get_forum(
    access_token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    forum_uuid: str,
    db: Session = Depends(get_db)
    ):
    try:
        refresh_token = request.cookies.get('REFRESH_TOKEN')
        payload, access_token = security.verify_access_token(refresh_token, access_token)
        payload = schemas.TokenData(**payload)
        forums = dbops.get_forum(forum_uuid, db)
        response.status_code = status.HTTP_200_OK
        return { "data": forums, "access_token": access_token }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

def main():
    from dotenv import load_dotenv
    import uvicorn
    load_dotenv()
    uvicorn.run("main:app", port=8000, reload=True)

if __name__ == "__main__":
    main()
