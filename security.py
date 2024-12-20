from datetime import timedelta, datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any
import jwt, consts as consts, hashlib, uuid, os, smtplib, ssl

def generate_refresh_token(expiry_date: timedelta | None = None) -> str:
    to_encode = {
        "token_type": "refresh"
    }
    if expiry_date:
        expire = datetime.now(timezone.utc) + expiry_date
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, consts.SECRET_KEY, algorithm=consts.ALGORITHM)

def generate_access_token(payload: dict, expiry_date: timedelta | None = None) -> str:
    to_encode = dict(payload).copy()
    if expiry_date:
        expire = datetime.now(timezone.utc) + expiry_date
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, consts.SECRET_KEY, algorithm=consts.ALGORITHM)

def verify_access_token(refresh_token: str, access_token: str) -> dict:
    try:
        access_data = jwt.decode(access_token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM])
        return access_data, None
    except jwt.ExpiredSignatureError or jwt.InvalidSignatureError:
        try:
            jwt.decode(refresh_token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM])
            access_data = jwt.decode(access_token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM], options=({"verify_signature": False}))
            access_token = generate_access_token(access_data)
            return access_data, access_token
        except jwt.ExpiredSignatureError or jwt.InvalidSignatureError:
            raise Exception("Invalid token")

def verify_refresh_token(token: str) -> dict:
    return jwt.decode(token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM], audience="refresh")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_uuid():
    return uuid.uuid4()

def get_locale_datetime():
    asia_utc = ZoneInfo("Asia/Singapore")
    return datetime.now(tz=asia_utc)

def send_email(email: str, subject: str, body: str):
    port = os.getenv('SMTP_PORT')
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SENDER_EMAIL')
    receiver_email = email
    password = os.getenv('SENDER_PASSWORD')
    message = 'Subject: {}\n\n{}'.format(subject, body)
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
