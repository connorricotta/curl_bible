from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from curl_bible import schema
from curl_bible.config import Options
from curl_bible.database import engine, get_database_session

app = FastAPI()

schema.Base.metadata.create_all(bind=engine)

REGULAR_TO_SUPERSCRIPT = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
}


class UserError(HTTPException):
    def __init__(self, detail: str):
        self.detail = detail
        self.status_code = status.HTTP_400_BAD_REQUEST


class ProgrammerError(HTTPException):
    def __init__(self, detail: str):
        self.detail = detail
        self.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


@app.get("/{book}/{chapter}")
async def entire_chapter(
    book: str,
    chapter: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    arguments = flatten_args(
        db=db,
        book=book,
        chapter=chapter,
        options=options,
    )
    return multi_query(db=db, **arguments)


@app.get("/{book}/{chapter}/{verse}")
async def flatten_out(
    book: str,
    chapter: str,
    verse: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    arguments = flatten_args(
        db, book=book, chapter=chapter, verse=verse, options=options
    )
    return multi_query(db, **arguments)


@app.get("/{book}/{chapter}/{verse_start}/{verse_end}")
async def mutli_verse_same_chapter(
    book: str,
    chapter: str,
    verse_start: str,
    verse_end: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    arguments = flatten_args(
        db=db,
        book=book,
        chapter=chapter,
        verse_start=verse_start,
        verse_end=verse_end,
        options=options,
    )
    return multi_query(db=db, **arguments)


@app.get("/{book}/{chapter_start}/{verse_start}/{chapter_end}/{verse_end}")
async def mutli_verse_different_chapter(
    book: str,
    chapter_start: str,
    verse_start: str,
    chapter_end: str,
    verse_end: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    arguments = flatten_args(
        db=db,
        book=book,
        chapter_start=chapter_start,
        chapter_end=chapter_end,
        verse_start=verse_start,
        verse_end=verse_end,
        options=options,
    )
    return multi_query(db=db, **arguments)


def multi_query(db, **kwargs) -> str:
    options = kwargs.pop("options")
    if options is not None:
        if options.version == "ASV":
            version = schema.TableASV
        elif options.version == "BBE":
            version = schema.TableBBE
        elif options.version == "JKV":
            version = schema.TableKJV
        elif options.version == "WEB":
            version = schema.TableWEB
        elif options.version == "YLT":
            version = schema.TableYLT
    else:
        version = schema.TableASV

    # Query single verse
    if set(["book", "chapter", "verse"]) == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
                .filter(version.verse == kwargs.get("verse"))
            ).all()

        except Exception as e:
            raise ProgrammerError(repr(e))

    # Entire chapter
    elif set(["book", "chapter"]) == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
            ).all()
        except Exception as e:
            raise ProgrammerError(repr(e))

    # Multi verse, same chapter
    elif set(["book", "chapter", "verse_start", "verse_end"]) == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
                .filter(
                    version.verse.between(
                        kwargs.get("verse_start"), kwargs.get("verse_end")
                    )
                )
            ).all()
        except Exception as e:
            raise ProgrammerError(repr(e))

    # Multi verse, different chapter
    elif set(
        ["book", "chapter_start", "chapter_end", "verse_start", "verse_end"]
    ) == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(
                    version.chapter.between(
                        kwargs.get("chapter_start"), kwargs.get("chapter_end")
                    )
                )
                .filter(
                    version.id.between(
                        "".join(
                            [
                                kwargs.get("book"),
                                kwargs.get("chapter_start"),
                                kwargs.get("verse_start"),
                            ]
                        ),
                        "".join(
                            [
                                kwargs.get("book"),
                                kwargs.get("chapter_end"),
                                kwargs.get("verse_end"),
                            ]
                        ),
                    )
                )
            ).all()
        except Exception as e:
            raise ProgrammerError(repr(e))
    else:
        raise UserError("verse not found")
    if data is not None:
        if options.verse_numbers:
            # Converts verse numbers into their uppercase version
            return " ".join(
                [
                    "".join(
                        [REGULAR_TO_SUPERSCRIPT.get(num) for num in [*str(query.verse)]]
                    )
                    + query.text
                    for query in data
                ]
            )
        elif False:
            # JSON Response
            # TODO: finish this with proper queries
            text = " ".join([query.text for query in data])
            kwargs.update({"text": text})
            return kwargs
        else:
            return " ".join([query.text for query in data])


def flatten_args(db, **kwargs):
    """
    Convert regular bible verses into IDs
    """

    for argument in [
        "chapter",
        "chapter_start",
        "chapter_end",
        "verse",
        "verse_start",
        "verse_end",
    ]:
        if argument in kwargs.keys():
            if not str.isnumeric(kwargs.get(argument)):
                raise UserError(f"Invalid {argument}! {argument} is not a number!")
            kwargs[argument] = "0" * (3 - len(kwargs.get(argument))) + kwargs.get(
                argument
            )

    if "book" in kwargs.keys():
        data = (
            db.query(schema.KeyAbbreviationsEnglish)
            .filter(schema.KeyAbbreviationsEnglish.name == kwargs.get("book"))
            .filter(schema.KeyAbbreviationsEnglish.primary == "1")
        ).first()
        if data is not None:
            kwargs["book"] = str(data.book)
        else:
            raise UserError(f"Book {kwargs.get('book')} not found.")

    return kwargs
