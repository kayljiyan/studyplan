# modules used
# from dotenv import load_dotenv
import os

# loads the environment variables
# load_dotenv()

# environment variables
SECRET_KEY: str = os.environ.get('SECRET_KEY')
ALGORITHM: str = "HS256"
REFRESH_TOKEN_EXPIRE_DAYS: int = 7
ACCESS_TOKEN_EXPIRE_HOURS: int = 1
