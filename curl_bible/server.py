from random import choice, randint
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from curl_bible import __version__, schema

# from curl_bible.config import Options, create_book
from curl_bible.config import Options, Settings, create_book, create_request_verse
from curl_bible.database import engine, get_database_session

settings = Settings()
app = FastAPI(version=__version__)

schema.Base.metadata.create_all(bind=engine)


class UserError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ProgrammerError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


@app.get("/")
async def as_arguments_book_chapter_verse(
    book: Union[str | None] = Query(default=None),
    chapter: Union[int, None] = Query(default=None, ge=0, le=50),
    verse: Union[str, None] = Query(default=None, regex=settings.VERSE_REGEX),
    db_session: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()
    if book is None and chapter is None and verse is None:
        book = choice(["Matthew", "Mark", "Luke", "John", "Rev"])
        chapter = str(randint(1, 10))
        verse = f"{randint(1,5)}-{randint(6,10)}"
    if book is not None:
        kwargs["book"] = book
    if chapter is not None:
        kwargs["chapter"] = chapter
    if verse is not None:
        if "-" in verse:
            verse_start, verse_end = verse.split("-")
            kwargs["verse_start"] = verse_start
            kwargs["verse_end"] = verse_end
        else:
            kwargs["verse"] = verse

    request_verse = create_request_verse(**kwargs)
    arguments = flatten_args(db=db_session, options=options, **kwargs)

    kwargs.update(multi_query(db_session, **arguments))

    if options.return_json:
        kwargs["request_verse"] = request_verse
        return kwargs
    else:
        result = create_book(
            bible_verse=kwargs.get("text"),
            user_options=options,
            request_verse=request_verse,
        )
    return PlainTextResponse(content=result)


@app.get("/{query}")
async def query_many(
    query: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()
    split_query = query.split(":")
    if len(split_query) == 2:
        kwargs["book"] = split_query[0]
        kwargs["chapter"] = split_query[1]
    elif len(split_query) == 3:
        kwargs["book"] = split_query[0]
        kwargs["chapter"] = split_query[1]
        if "-" in split_query[2]:
            verse_start, verse_end = split_query[2].split("-")
            kwargs["verse_start"] = verse_start
            kwargs["verse_end"] = verse_end
        else:
            kwargs["verse"] = split_query[2]

    request_verse = create_request_verse(**kwargs)
    arguments = flatten_args(db=db, options=options, **kwargs)

    kwargs.update(multi_query(db, **arguments))

    if options.return_json:
        kwargs["request_verse"] = request_verse
        return kwargs
    elif options.text_only:
        return PlainTextResponse(content=kwargs.get("text"))
    else:
        result = create_book(
            bible_verse=kwargs.get("text"),
            user_options=options,
            request_verse=request_verse,
        )
        return PlainTextResponse(content=result)


@app.get("/{book}/{chapter}")
async def entire_chapter(
    book: str,
    chapter: str,
    db_session: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()
    arguments = flatten_args(
        db=db_session,
        book=book,
        chapter=chapter,
        options=options,
    )
    request_verse = create_request_verse(book=book, chapter=chapter)
    kwargs.update(multi_query(db_session, **arguments))

    if options.return_json:
        kwargs["request_verse"] = request_verse
        return kwargs
    else:
        result = create_book(
            bible_verse=kwargs.get("text"),
            user_options=options,
            request_verse=request_verse,
        )
    return PlainTextResponse(content=result)


@app.get("/{book}/{chapter}/{verse}")
async def flatten_out(
    book: str,
    chapter: str,
    verse: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()

    if "-" in verse:
        verse_start, verse_end = verse.split("-")
        request_verse = create_request_verse(
            book=book, chapter=chapter, verse_start=verse_start, verse_end=verse_end
        )
        arguments = flatten_args(
            db,
            book=book,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end,
            options=options,
        )
    else:
        request_verse = create_request_verse(book=book, chapter=chapter, verse=verse)
        arguments = flatten_args(
            db,
            book=book,
            chapter=chapter,
            verse=verse,
            options=options,
        )

    kwargs.update(multi_query(db, **arguments))

    if options.return_json:
        kwargs["request_verse"] = request_verse
        return kwargs
    else:
        result = create_book(
            bible_verse=kwargs.get("text"),
            user_options=options,
            request_verse=request_verse,
        )
    return PlainTextResponse(content=result)


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
    book_text = multi_query(db, **arguments)
    result = create_book(
        bible_verse=book_text.get("text"),
        user_options=options,
        request_verse=f"{book} {chapter}:{verse_start}-{verse_end}",
    )
    return PlainTextResponse(content=result)


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
    if {"book", "chapter", "verse"} == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
                .filter(version.verse == kwargs.get("verse"))
            ).all()

        except Exception as e:
            raise ProgrammerError(repr(e)) from e

    # Entire chapter
    elif {"book", "chapter"} == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
            ).all()

        except Exception as e:
            raise ProgrammerError(repr(e)) from e

    # Multi verse, same chapter
    elif {"book", "chapter", "verse_start", "verse_end"} == set(kwargs.keys()):
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
            raise ProgrammerError(repr(e)) from e

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
            raise ProgrammerError(repr(e)) from e
    else:
        raise UserError("verse not found")
    if data is not None:
        if options.verse_numbers:
            # Converts verse numbers into their uppercase version
            text = " ".join(
                [
                    "".join(
                        [
                            settings.REGULAR_TO_SUPERSCRIPT.get(num)
                            for num in [*str(query.verse)]
                        ]
                    )
                    + query.text
                    for query in data
                ]
            )
            kwargs["text"] = text
            kwargs["options"] = options
            return kwargs
        # elif False:
        # JSON Response
        # TODO: finish this with proper queries
        #     text = " ".join([query.text for query in data])
        #     kwargs.update({"text": text})
        #     return kwargs
        else:
            text = " ".join([query.text for query in data])
            kwargs["text"] = text
            kwargs["options"] = options
            return kwargs


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
            if type(kwargs.get(argument)) == int:
                kwargs[argument] = str(kwargs.get(argument))
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
