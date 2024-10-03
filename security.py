from datetime import timedelta, datetime, timezone
from typing import Any
import jwt, consts as consts, hashlib, uuid, os, smtplib, ssl

def generate_refresh_token(payload: dict, expiry_date: timedelta | None = None) -> str:
    to_encode = payload.copy()
    if expiry_date:
        expire = datetime.now(timezone.utc) + expiry_date
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, consts.SECRET_KEY, algorithm=consts.ALGORITHM)

def generate_access_token(payload: dict, expiry_date: timedelta | None = None) -> str:
    to_encode = payload.copy()
    if expiry_date:
        expire = datetime.now(timezone.utc) + expiry_date
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, consts.SECRET_KEY, algorithm=consts.ALGORITHM)

def verify_access_token(token: str) -> dict:
    return jwt.decode(token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_uuid():
    return uuid.uuid4()

def send_email(email: str):
    port = os.getenv('SMTP_PORT')
    smtp_server = os.getenv('SMTP_SERVER')
    sender_email = os.getenv('SENDER_EMAIL')
    receiver_email = email
    password = os.getenv('SENDER_PASSWORD')
    print(sender_email)
    SUBJECT = "Email Confirmation"
    TEXT = f"""
    Confirm your email with the link below.

    http://127.0.0.1:8000/api/v1/confirm/{email}"""
    message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
