import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST=os.environ.get('DB_HOST')
    DB_PORT=os.environ.get('DB_PORT')
    DB_NAME=os.environ.get('DB_NAME')
    DB_USER=os.environ.get('DB_USER')
    DB_PASSWORD=os.environ.get('DB_PASSWORD')
    SECRET_KEY=os.environ.get('DB_HOST')