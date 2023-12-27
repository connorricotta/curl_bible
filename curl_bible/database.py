from socket import IPPROTO_TCP, gaierror, getaddrinfo
from time import sleep

from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta

# from config import create_database_settings


# db_settings = create_database_settings()
class DatabaseSettings(BaseSettings):
    DEBUG: bool
    DB_CONNECT_ATTEMPTS: int
    MYSQL_USERNAME: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_DATABASE: str
    MYSQL_DB_PORT: int

    class Config:
        env_file = ".env"


db_settings = DatabaseSettings()

# Turn DNS into IP address
try:
    address_info = getaddrinfo(db_settings.MYSQL_HOST, 3306, proto=IPPROTO_TCP)
    db_settings.MYSQL_HOST = address_info[-1][-1][0]
    print(f"Got db_host of {db_settings.MYSQL_HOST} ")
except gaierror:
    db_settings.MYSQL_HOST = "localhost"

SQLALCHEMY_DATABASE_URL = f"mariadb+mariadbconnector://{db_settings.MYSQL_USERNAME}:{db_settings.MYSQL_PASSWORD}@{db_settings.MYSQL_HOST}:{db_settings.MYSQL_DB_PORT}/{db_settings.MYSQL_DATABASE}?charset=utf8mb4"

if not db_settings.DEBUG:
    sleep(30)
for i in range(db_settings.DB_CONNECT_ATTEMPTS):
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        if isinstance(Base, DeclarativeMeta):
            break
    except Exception:
        print(f"Unable to connect on attempt {i}")
        sleep(10)

if Base is None:
    # Connect to localhost as a last ditch effort
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        db_settings.MYSQL_HOST, "localhost"
    )
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()


def get_database_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
