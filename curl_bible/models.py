from pydantic import BaseModel


class Hero(BaseModel):
    id = int
    name = str
    secret_name = str
    age = int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    password: str


class KeyAbbreviationsEnglish(BaseModel):
    id = int
    a = str
    b = int
    p = int

    class Config:
        orm_mode = True


class TableASV(BaseModel):
    id = int
    book = int
    chapter = int
    verse = int
    text = str

    class Config:
        orm_mode = True


class TableBBE(BaseModel):
    id = int
    book = int
    chapter = int
    verse = int
    text = str

    class Config:
        orm_mode = True


class Meta(BaseModel):
    status: str
    message: str


class DBReturn(BaseModel):
    meta: Meta
    content: str


class TableKJV(BaseModel):
    id = int
    book = int
    chapter = int
    verse = int
    text = str

    class Config:
        orm_mode = True


class TableWEB(BaseModel):
    id = int
    book = int
    chapter = int
    verse = int
    text = str

    class Config:
        orm_mode = True


class TableYLT(BaseModel):
    id = int
    book = int
    chapter = int
    verse = int
    text = str

    class Config:
        orm_mode = True
