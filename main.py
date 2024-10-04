from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
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
    allow_origins="*",
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
        data = { "user_uuid": f'{account.user_uuid}', "user_email": account.user_email }
        refresh_token_expiry_date = timedelta(days=consts.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = security.generate_refresh_token(data, refresh_token_expiry_date)
        response.status_code = status.HTTP_200_OK
        response.set_cookie(key="SET_REFRESH_TOKEN", value=refresh_token)
        response.set_cookie(key="SET_REFRESH_TYPE", value="Bearer")
        return {"detail": "Login successful"}
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
        response.status_code = status.HTTP_202_ACCEPTED
        return { 'detail': 'Email has been confirmed' }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/access')
async def get_access_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    response: Response
    ):
    try:
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        data = payload
        access_token_expiry_date = timedelta(hours=consts.ACCESS_TOKEN_EXPIRE_HOURS)
        access_token = security.generate_access_token(data, access_token_expiry_date)
        response.status_code = status.HTTP_200_OK
        return { "access_token": access_token, "access_type": "Bearer" }
    except Exception as e:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return { "detail": str(e) }

@app.post('/api/v1/task')
async def create_task(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        data = await request.json()
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        data = {**data, 'user_uuid': payload.user_uuid}
        task = schemas.TaskAddToDB(**data)
        dbops.create_task(db, task)
        response.status_code = status.HTTP_201_CREATED
        return { "detail": "Task has been created" }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.patch('/api/v1/task')
async def update_task(
    token: Annotated[str, Depends(oauth2_scheme)],
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        data = await request.json()
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        data = {**data, 'user_uuid': payload.user_uuid}
        task = schemas.TaskUpdateToDB(**data)
        dbops.update_task(db, task)
        response.status_code = status.HTTP_202_ACCEPTED
        return { "detail": "Task has been updated" }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.patch('/api/v1/task/{task_uuid}')
async def complete_task(
    token: Annotated[str, Depends(oauth2_scheme)],
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        dbops.complete_task(db, task_uuid, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return { "detail": "Task has been completed" }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.delete('/api/v1/task/{task_uuid}')
async def delete_task(
    token: Annotated[str, Depends(oauth2_scheme)],
    task_uuid: str,
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        dbops.delete_task(db, task_uuid, payload.user_uuid)
        response.status_code = status.HTTP_204_NO_CONTENT
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/tasks')
async def get_tasks(
    token: Annotated[str, Depends(oauth2_scheme)],
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        tasks = dbops.get_tasks(db, payload.user_uuid)
        response.status_code = status.HTTP_200_OK
        return { "data": tasks }
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
