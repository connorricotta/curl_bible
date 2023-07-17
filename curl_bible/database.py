from os import getenv
from socket import IPPROTO_TCP, getaddrinfo
from time import sleep

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
username = getenv("MYSQL_USER")
password = getenv("MYSQL_PASSWORD")
db_host = getenv("MYSQL_HOST")
db_name = getenv("MYSQL_DATABASE")
db_port = getenv("MYSQL_DB_PORT")


# Turn DNS into IP address
try:
    s = getaddrinfo(db_host, 3306, proto=IPPROTO_TCP)
    db_host = s[-1][-1][0]
except Exception:
    pass


# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = f"mariadb+mariadbconnector://{username}:{password}@{db_host}/{db_name}?charset=utf8mb4"

# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://test:password@localhost/hero?charset=utf8mb4"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

try:
    # sleep(10)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    pass
    db_host = "localhost"
    SQLALCHEMY_DATABASE_URL = f"mariadb+mariadbconnector://{username}:{password}@{db_host}/{db_name}?charset=utf8mb4"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_database_session():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
