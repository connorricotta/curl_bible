from pydantic import BaseModel, ConfigDict

# These are the Pydantic models for the database


class KeyAbbreviationsEnglish(BaseModel):
    id: int
    name: str
    book: int
    primary: bool
    model_config: ConfigDict(from_attributes=True)


class TableASV(BaseModel):
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    model_config: ConfigDict(from_attributes=True)


class TableBBE(BaseModel):
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    model_config: ConfigDict(from_attributes=True)


class Meta(BaseModel):
    status: str
    message: str


class DBReturn(BaseModel):
    meta: Meta
    content: str


class TableKJV(BaseModel):
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    model_config: ConfigDict(from_attributes=True)


class TableWEB(BaseModel):
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    model_config: ConfigDict(from_attributes=True)


class TableYLT(BaseModel):
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    model_config: ConfigDict(from_attributes=True)
