from random import choice, randint
from typing import Union

from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from curl_bible.config import (
    Options,
    __version__,
    create_book,
    create_request_verse,
    create_settings,
    flatten_args,
    multi_query,
)
from curl_bible.database import engine, get_database_session

# from schema.Base import metadata
from curl_bible.db_models import Base
from curl_bible.helper_methods import router as helper_methods_router

limiter = Limiter(key_func=get_remote_address)
settings = create_settings()

app = FastAPI(version=__version__, docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="curl_bible/static"), name="static")
app.include_router(helper_methods_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initalize DB
Base.metadata.create_all(bind=engine)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/")
@limiter.limit(settings.RATE_LIMIT)
async def as_arguments_book_chapter_verse(
    request: Request,
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
    kwargs["request"] = request
    arguments = flatten_args(db=db_session, options=options, **kwargs)

    kwargs.update(multi_query(db_session, **arguments))

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


@app.get("/{query}")
@limiter.limit(settings.RATE_LIMIT)
async def query_many(
    request: Request,
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
    kwargs["request"] = request
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
@limiter.limit(settings.RATE_LIMIT)
async def entire_chapter(
    request: Request,
    book: str,
    chapter: str,
    db_session: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()
    arguments = flatten_args(
        db=db_session, book=book, chapter=chapter, options=options, request=request
    )
    request_verse = create_request_verse(book=book, chapter=chapter)
    kwargs.update(multi_query(db_session, **arguments))

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


@app.get("/{book}/{chapter}/{verse}")
@limiter.limit(settings.RATE_LIMIT)
async def flatten_out(
    request: Request,
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
            book=book,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end,
        )
        arguments = flatten_args(
            db,
            book=book,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end,
            options=options,
            request=request,
        )
    else:
        request_verse = create_request_verse(book=book, chapter=chapter, verse=verse)
        arguments = flatten_args(
            db,
            book=book,
            chapter=chapter,
            verse=verse,
            options=options,
            request=request,
        )

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


@app.get("/{book}/{chapter}/{verse_start}/{verse_end}")
@limiter.limit(settings.RATE_LIMIT)
async def mutli_verse_same_chapter(
    request: Request,
    book: str,
    chapter: str,
    verse_start: str,
    verse_end: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    kwargs = dict()
    request_verse = create_request_verse(
        book=book, chapter=chapter, verse_start=verse_start, verse_end=verse_end
    )
    arguments = flatten_args(
        db=db,
        book=book,
        chapter=chapter,
        verse_start=verse_start,
        verse_end=verse_end,
        options=options,
        request=request,
    )
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


@app.get("/versions")
@limiter.limit(settings.RATE_LIMIT)
def show_bible_versions(request: Request):
    """
    Return a list of the bibles supported by this webapp.
    Taken from the 'bible_version_key' table in the DB.

    Args
        None
    Returns:
        (str): A string containing the help message
    Raises:
        None
    """
    return PlainTextResponse(
        content="""
    All current supported versions of the Bible.
    Use the value in 'Version Name' to use that version of the bible, such as:
        curl bible.ricotta.dev/John:3:15-19?version=BBE
        curl bible.ricotta.dev/John:3:15-19?options=version=BBE
    King James Version (KVJ) is the default version

    ╭──────────────┬──────────┬─────────────────────────────┬───────────────╮
    │ Version Name │ Language │ Name of version             │ Copyright     │
    ├──────────────┼──────────┼─────────────────────────────┼───────────────┤
    │     ASV      │ English  │ American Standard Version   │ Public Domain │
    │     BBE      │ English  │ Bible in Basic English      │ Public Domain │
    │     KJV      │ English  │ King James Version          │ Public Domain │
    │     WEB      │ English  │ World English Bible         │ Public Domain │
    │     YLT      │ English  │ Young's Literal Translation │ Public Domain │
    ╰──────────────┴──────────┴─────────────────────────────┴───────────────╯
""",
        status_code=status.HTTP_200_OK,
    )


@app.get("/help")
@limiter.limit(settings.RATE_LIMIT)
def display_help(request: Request):
    """
    Display a help message detailing all supported query methods and options.

    Args:
        None
    Returns:
        book(str): A string containg all supported query methods and options.
    Raises:
        None
    """
    return PlainTextResponse(
        content="""
   ______           __   ____  _ __    __
  / ____/_  _______/ /  / __ )(_) /_  / /__
 / /   / / / / ___/ /  / __  / / __ \\/ / _ \\
/ /___/ /_/ / /  / /  / /_/ / / /_/ / /  __/
\\____/\\__,_/_/  /_/  /_____/_/_.___/_/\\___/

Curl Bible - Easily access the bible through curl (HTTPie is also supported)

Supports the following query types (GET):
    • curl bible.ricotta.dev/John:3:15-19
    • curl bible.ricotta.dev/John/3/15-19
    • curl "bible.ricotta.dev?book=John&chapter=3&verse=15-19"
    • curl bible.ricotta.dev/John:3:15:John:4:15

The following options are supported:
    • 'l' or 'length' - the number of lines present in the book
        default value: 20

    • 'w' or 'width' - how many characters will be displayed in each line of the book.
        default value: 80

    • 'c' or 'color_text' - display the returned book with terminal colors
        default value: True

    • 't' or 'text_only' - only returned the unformatted text.
        deafult value: False

    • 'n' or 'verse_number' - Display the associated verse numbers in superscript.
        Default value: False

    • 'v' or 'version' - choose which version of the bible to use.
        Default value: ASV (American Standard Version)
        Tip: curl bible.ricotta.dev/versions to see all supported bible versions.

    • 'j' or 'return_json' - Return the JSON version of the response.

    These options can be combined on a single parameter for convenience:
        curl bible.ricotta.dev/John:3:15?options=l=50,w=85,c=False,v=BBE,j=True
    But may also be separated in key value pairs as parameters:
        curl "bible.ricotta.dev/John:3:15?length=40&color_text=False"
Check out the interactive help menu here: https://bible.ricotta.dev/docs

Full information can be found on the README here: https://github.com/connorricotta/curl_bible
""",
        status_code=status.HTTP_200_OK,
    )
