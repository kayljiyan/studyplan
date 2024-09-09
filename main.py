from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from datetime import timedelta
import models, schemas, dbops, security, consts
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
def login(
    request: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_db)
    ):
    try:
        account = dbops.login(db,request.username,request.password)
        if (account is not None):
            print(f'{account.user_uuid}')
            data = { "user_uuid": f'{account.user_uuid}', "user_email": account.user_email }
            access_token_expiry_date = timedelta(days=consts.ACCESS_TOKEN_EXPIRE_DAYS)
            access_token = security.generate_access_token(data, access_token_expiry_date)
            response.status_code = status.HTTP_200_OK
            return { "access_token": access_token, "access_type": "Bearer" }
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.headers["WWW-Authenticate"] = "Bearer"
            return { "detail": "Incorrect username or password" }
    except Exception as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return { "detail": str(e) }

@app.get('/api/v1/deserialize')
async def deserialize(token: Annotated[str, Depends(oauth2_scheme)], response: Response):
    try:
        payload = security.verify_access_token(token)
        payload = schemas.TokenData(**payload)
        data = payload
        response.status_code = status.HTTP_200_OK
        return { 'data': data }
    except Exception as e:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return { "detail": str(e) }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
