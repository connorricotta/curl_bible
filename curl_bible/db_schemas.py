from pydantic import BaseModel

# These are the Pydantic models for the database


class KeyAbbreviationsEnglish(BaseModel):
    id: int
    name: str
    book: int
    primary: bool

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
