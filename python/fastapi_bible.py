from re import search
from typing import Union

from fastapi import Depends, FastAPI, Path, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# Matches '3','999','1-999','999-1'
VERSE_REGEX = "^(([0-9]{1,3})|([0-9]{1,3}-[0-9]{1,3}))$"
# Matches 'John:3:5','Psalms:119:175'
SINGLE_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:5:John:4:3', 'Numbers:7:1:Psalms:119:175'
MULTI_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}:[A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:1-2','Psalms:119:170-176'
SINGLE_SEMICOLON_DASH_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}-[0-9]{1,3})$"


class Options(BaseModel):
    def __init__(self, **data):
        super().__init__(
            color=data.get("nc") or data.get("color"),
            text_only=data.get("t") or data.get("text_only"),
            version=data.get("v") or data.get("version"),
            length=data.get("l") or data.get("length"),
            width=data.get("w") or data.get("width"),
        )

    color: Union[bool, str, None]
    text_only: Union[bool, str, None]
    version: str | None = Query(min_length=3, max_length=3)
    length: int | None = Path(gt=0, default=20)
    width: int | None = Path(gt=0, default=80)


@app.get("/")
async def parse_arguments_quote(book: str, chapter: int, verse: str):
    verse_num = validate_verses([verse])
    if verse_num != 0:
        return Response(
            content=f"verse {verse_num} is not a verse. Accepted values include '3','15','3-19'\n",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return {"book": book, "chapter": chapter, "verse": verse}


@app.get("/{quote}")
async def parse_semicolon_quote(quote: str):
    if search(SINGLE_SEMICOLON_REGEX, quote) is None:
        if search(SINGLE_SEMICOLON_DASH_REGEX, quote) is None:
            if search(MULTI_SEMICOLON_REGEX, quote) is None:
                """
                A more 'proper' HTTPException or JSONResponse is not raised because
                this application will be used in the terminal by humans,
                and so must use plaintext responses.
                """
                return Response(
                    content="Value is not a proper quote. Please refer to bible.ricotta.dev/help\n",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            return {"type": "multi"}
        return {"type", "single with dash"}
    return {"type": "single no dash"}


@app.get("/{book}/{chapter}/{verse}")
async def parse_single_slash_quote(
    book: str = Query(default=..., min_length=4, max_length=20),
    chapter: int = Field(default=..., ge=0, lt=1000),
    verse: str = Query(default=..., min_length=1, max_length=7),
):
    verse_num = validate_verses([verse])
    if verse_num != 0:
        return Response(
            content=f"verse {verse_num} is not a verse. Accepted values include '3','15','3-19'\n",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return {"book": book, "chapter": chapter, "verse": verse}


@app.get("/{book_1}/{chapter_1}/{verse_1}/{book_2}/{chapter_2}/{verse_2}")
async def parse_multi_slash_quote(
    book_1: str,
    book_2: str,
    chapter_1: int,
    chapter_2: int,
    verse_1: str,
    verse_2: str,
):
    verse_num = validate_verses([verse_1, verse_2])
    if verse_num != 0:
        return Response(
            content=f"Verse {verse_num} is not a verse. Accepted values include '3','15','159'\n",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return {
        "book_1": book_1,
        "chapter_1": chapter_1,
        "book_2": book_2,
        "chapter_2": chapter_2,
        "verse_1": verse_1,
        "verse_2": verse_2,
    }


def validate_verses(verse_list: list) -> int:
    """
    Iterates through each verse to make sure it is valid.
    Returns (int):
        0 - All Verses valid
        1 - Verse 1 Invalid
        2 - Verse 2 Invalid
    """
    for count, verse in enumerate(verse_list):
        if search(VERSE_REGEX, verse) is None:
            return count + 1
    else:
        return 0
