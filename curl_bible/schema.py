from sqlalchemy import Column, Integer, String

from curl_bible.database import Base

# from sqlalchemy import Boolean, Column, ForeignKey, Integer,
# from sqlalchemy.orm import relationship


class Hero(Base):
    __tablename__ = "hero"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(255))
    secret_name = Column(String(255))
    age = Column(Integer())


class KeyAbbreviationsEnglish(Base):
    __tablename__ = "key_abbrevations_english"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    a = Column(String(255))
    b = Column(Integer())
    p = Column(Integer())


class TableASV(Base):
    __tablename__ = "t_asv"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    book = Column(Integer())
    chapter = Column(Integer())
    verse = Column(Integer())
    text = Column(String(255))


class TableBBE(Base):
    __tablename__ = "t_bbe"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    book = Column(Integer())
    chapter = Column(Integer())
    verse = Column(Integer())
    text = Column(String(255))


class TableKJV(Base):
    __tablename__ = "t_kjv"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    book = Column(Integer())
    chapter = Column(Integer())
    verse = Column(Integer())
    text = Column(String(255))


class TableWEB(Base):
    __tablename__ = "t_web"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    book = Column(Integer())
    chapter = Column(Integer())
    verse = Column(Integer())
    text = Column(String(255))


class TableYLT(Base):
    __tablename__ = "t_ylt"
    id = Column(Integer(), primary_key=True, autoincrement=True)
    book = Column(Integer())
    chapter = Column(Integer())
    verse = Column(Integer())
    text = Column(String(255))
