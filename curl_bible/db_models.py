from sqlalchemy import Boolean, Column, Integer, String

from curl_bible.database import Base

# These are the DB models for querying


class KeyAbbreviationsEnglish(Base):
    __tablename__ = "key_abbreviations_english"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    book = Column(Integer)
    primary = Column(Boolean)


class TableASV(Base):
    __tablename__ = "t_asv"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book = Column(Integer)
    chapter = Column(Integer)
    verse = Column(Integer)
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
