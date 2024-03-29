from socket import IPPROTO_TCP, gaierror, getaddrinfo
from time import sleep

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta


class DatabaseSettings(BaseSettings):
    DEBUG: bool
    DB_CONNECT_ATTEMPTS: int
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_DATABASE: str
    MYSQL_DB_PORT: int
    MYSQL_ROOT_USER: str
    MYSQL_ROOT_PASSWORD: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


db_settings = DatabaseSettings()

# Turn DNS into IP address
try:
    address_info = getaddrinfo(db_settings.MYSQL_HOST, 3306, proto=IPPROTO_TCP)
    db_settings.MYSQL_HOST = address_info[-1][-1][0]
    print(f"Got db_host of {db_settings.MYSQL_HOST} ")
except gaierror:
    db_settings.MYSQL_HOST = "localhost"

SQLALCHEMY_DATABASE_URL = f"mariadb+mariadbconnector://{db_settings.MYSQL_USER}:{db_settings.MYSQL_PASSWORD}@{db_settings.MYSQL_HOST}:{db_settings.MYSQL_DB_PORT}/{db_settings.MYSQL_DATABASE}?charset=utf8mb4"

if not db_settings.DEBUG:
    sleep(30)
for i in range(db_settings.DB_CONNECT_ATTEMPTS):
    try:
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, pool_recycle=360
        )
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
