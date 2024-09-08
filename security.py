from datetime import timedelta, datetime, timezone
from typing import Any
import jwt, consts

def generate_access_token(payload: dict, expiry_date: timedelta | None = None) -> str:
    """
    Generates an access token

    Args:
        payload (dict): the payload to be encoded
        expiry_date (timedelta | None, optional): the expiry date of the token. Defaults to None.
    """
    to_encode = payload.copy()
    if expiry_date:
        expire = datetime.now(timezone.utc) + expiry_date
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, consts.SECRET_KEY, algorithm=consts.ALGORITHM)

def verify_access_token(token: str) -> dict:
    return jwt.decode(token, consts.SECRET_KEY, algorithms=[consts.ALGORITHM])
