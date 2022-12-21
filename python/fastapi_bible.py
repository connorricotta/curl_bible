# Standard Library Imports
from logging import basicConfig, critical, warning
from os import getenv, mkdir, path
from pathlib import Path
from re import search
from random import choice, randint

# Module Imports
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Query, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from mysql.connector import Error, connect
from starlette import requests
from typing import Union

# Sub-directory imports
from config import *

app = FastAPI()

# Send plain-text responses to error messages instead of JSON.
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return PlainTextResponse(
        content=str(exc) + "\n", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.on_event("startup")
async def startup():
    """
    Pulls required information for the app to function properly.

    Ensured the .env file exists, and pulls the required values to connect to the database.
    Sets up the logger.

    Args:
        None
    Returns:
        None
    Raises:
        exit(1): Unable to find the .env file or DB parameters were not found.
    """
    global DB_CONFIG

    if not path.exists(".env"):
        critical("Cannot load DB config file, check README in GitHub repo")
        exit(1)
    dotenv_path = Path(".env")
    load_dotenv(dotenv_path=dotenv_path)

    if not path.exists("log"):
        mkdir("log")
    basicConfig(
        filename="log/bible.log",
        filemode="a",
        format="%(asctime)s | Level:%(levelname)s | Logger:%(name)s | Src:%(filename)s.%(funcName)s@%(lineno)d | Msg:%(message)s",
        datefmt="%m/%d/%y %I:%M:%S %p %z (%Z)",
    )

    DB_CONFIG = {
        "db_host": getenv("DB_HOST"),
        "db_dbname": getenv("MYSQL_DATABASE"),
        "db_user": getenv("MYSQL_USER"),
        "db_password": getenv("MYSQL_PASSWORD"),
        "db_port": getenv("DB_PORT"),
    }
    if None in DB_CONFIG.values():
        critical("All values from the .env file could not be pulled.")
        exit(1)


@app.get("/")
async def as_arguments_book_chapter_verse(
    request: requests.Request,
    book: Union[str, None] = Query(default=None, max_length=25),
    chapter: Union[int, None] = Query(default=None, ge=0, le=50),
    verse: Union[str, None] = Query(default=None, regex=VERSE_REGEX),
    options: Options = Depends(),
):
    """
    Either takes in a book, chapter, verse through query parameters, or randomly selects a bible passage and returns it.

    Type of query is determined by if the book, chapter, and verse is None.
    If it is a random query, it also includes a message to direct the user on how to use the application.

    Args:
        None
    Returns:
        book(str): A string containing the random verse with default options
    Raises:
        None
    """
    options.update(request)
    if book == None and chapter == None and verse == None:
        # Query random verse
        book = choice(["Matthew", "Mark", "Luke", "John", "Rev"])
        chapter = str(randint(1, 10))
        verse = f"{randint(1,5)}-{randint(6,10)}"
        options = Options()
        response, book = query_multiple_verses_one_chapter(
            book, chapter, verse, options
        )
        if response.is_error():
            return f"Unable to print verse. Reason {response.get_content()}"

        full_book = parse_db_response(
            result=response,
            user_options=options,
            queried_verse=f"{book} {chapter}:{verse}",
        )
    else:
        verse_num = validate_verses([verse])
        if verse_num != 0:
            return Response(
                content=f"Verse {verse_num} is not a verse. Accepted values include '3','15','159'\n",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if "-" in verse:
            response, book = query_multiple_verses_one_chapter(
                book, chapter, verse, options
            )
        else:
            response, book = query_single_verse(book, chapter, verse, options)
        # Query the DB
        if response.is_error():
            return f"Unable to print verse. Reason {response.get_content()}"

        # Render the book with all specified options
        full_book = parse_db_response(
            result=response,
            user_options=options,
            queried_verse=f"{book} {chapter}:{verse}",
        )
    return PlainTextResponse(content=full_book.get_content())


@app.get("/")
async def random():
    """
    Randomly selects a bible passage and returns it.

    Also includes a message to direct the user on how to use the application.

    Args:
        None
    Returns:
        book(str): A string containing the random verse with default options
    Raises:
        None
    """
    book = choice(["Matthew", "Mark", "Luke", "John", "Rev"])
    chapter = str(randint(1, 10))
    verse = f"{randint(1,5)}-{randint(6,10)}"
    options = Options()
    response, book = query_multiple_verses_one_chapter(book, chapter, verse, options)
    if response.is_error():
        return f"Unable to print verse. Reason {response.get_content()}"

    full_book = parse_db_response(
        result=response, user_options=options, queried_verse=f"{book} {chapter}:{verse}"
    )

    return PlainTextResponse(
        content=full_book.get_content()
        + "\nTry 'curl bible.ricotta.dev/help' for more information.\n"
    )


@app.get("/versions")
def show_bible_versions():
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
def display_help():
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

    • 'nc' or 'no_color' - display the returned book without terminal colors
        default value: False

    • 'c' or 'color' - display the returned book with terminal colors
        default value: True

    • 't' or 'text' - only returned the unformatted text.

    • 'v' or 'version' - choose which version of the bible to use.
        Default value: ASV (American Standard Version)
        Tip: curl bible.ricotta.dev/versions to see all supported bible versions.

    These options can be combined:
        curl bible.ricotta.dev/John:3:15:John:4:15?options=l=50,w=85,nc,v=BBE

Check out the interactive help menu here: https://bible.ricotta.dev/docs

Full information can be found on the README here: https://github.com/connorricotta/curl_bible
""",
        status_code=status.HTTP_200_OK,
    )


@app.get("/{quote}")
async def colon_delimited_book_chapter_verse(
    request: requests.Request, quote: str, options: Options = Depends()
):
    if search(SINGLE_SEMICOLON_REGEX, quote) is None:
        if search(SINGLE_SEMICOLON_DASH_REGEX, quote) is None:
            if search(MULTI_SEMICOLON_REGEX, quote) is None:
                if search(ENTIRE_CHAPTER_REGEX, quote) is None:
                    return Response(
                        content="Value is not a proper quote. Please refer to bible.ricotta.dev/help\n",
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    )
                # Entire chapter
                options.update(request)
                if len(quote.split(":")) != 2:
                    return Response(
                        content=f"Invalid query! '{quote}' is not made up of a Book:Chapter:Verse.",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                book, chapter = quote.split(":")
                response, book = query_entire_chapter(book, chapter, options)
                if response.is_error():
                    return f"Unable to print verse. Reason {response.get_content()}"

                # Render the book with all specified options
                full_book = parse_db_response(
                    result=response,
                    user_options=options,
                    queried_verse=f"{book} {chapter}",
                )
                return PlainTextResponse(content=full_book.get_content())

            # Multi quote
            options.update(request)
            if len(quote.split(":")) != 6:
                return Response(
                    content=f"Invalid query! '{quote}' is not made up of a Book:Chapter:Verse.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            # Parse request into arguments
            (book_1, chapter_1, verse_1, book_2, chapter_2, verse_2) = quote.split(":")
            response, book_1, book_2 = query_multiple_verses(
                starting_book=book_1,
                starting_chapter=chapter_1,
                starting_verse=verse_1,
                ending_book=book_2,
                ending_chapter=chapter_2,
                ending_verse=verse_2,
                options=options,
            )
            if response.is_error():
                return f"Unable to print verse. Reason {response.get_content()}"

            # Have the returned verse look nice.
            if book_1 == book_2 and chapter_1 != chapter_2:
                full_verse = f"{book_1} {chapter_1}:{verse_1}-{chapter_2}:{verse_2}"
            elif chapter_1 == chapter_2:
                full_verse = f"{book_1} {chapter_1}:{verse_1}-{verse_2}"
            else:
                full_verse = (
                    f"{book_1} {chapter_1}:{verse_1}-{book_2} {chapter_2}:{verse_2}"
                )
            # Render the book with all specified options
            full_book = parse_db_response(
                result=response,
                user_options=options,
                queried_verse=full_verse,
            )
            return PlainTextResponse(content=full_book.get_content())

        # Single WITH dash
        options.update(request)
        if len(quote.split(":")) != 3:
            return Response(
                content=f"Invalid query! '{quote}' is not made up of a Book:Chapter:Verse.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        book, chapter, verse = quote.split(":")
        # Query the DB
        response, book = query_multiple_verses_one_chapter(
            book, chapter, verse, options
        )
        if response.is_error():
            return f"Unable to print verse. Reason {response.get_content()}"

        # Render the book with all specified options
        full_book = parse_db_response(
            result=response,
            user_options=options,
            queried_verse=f"{book} {chapter}:{verse}",
        )
        return PlainTextResponse(content=full_book.get_content())

    # Single without dash
    options.update(request)
    if len(quote.split(":")) != 3:
        return Response(
            content=f"Invalid query! '{quote}' is not made up of a Book:Chapter:Verse.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    book, chapter, verse = quote.split(":")

    # Query the DB
    response, book = query_single_verse(book, chapter, verse, options)
    if response.is_error():
        return f"Unable to print verse. Reason {response.get_content()}"

    # Render the book with all specified options
    full_book = parse_db_response(
        result=response, user_options=options, queried_verse=f"{book} {chapter}:{verse}"
    )
    return PlainTextResponse(content=full_book.get_content())


@app.get("/{book}/{chapter}")
async def as_slashes_book_chapter(
    request: requests.Request,
    book: str = Query(default=..., min_length=4, max_length=20),
    chapter: int = Query(default=..., ge=0, lt=1000),
    options: Options = Depends(),
):
    options.update(request)
    response, book = query_entire_chapter(book, chapter, options)
    if response.is_error():
        return f"Unable to print verse. Reason {response.get_content()}"

    # Render the book with all specified options
    full_book = parse_db_response(
        result=response, user_options=options, queried_verse=f"{book} {chapter}"
    )
    return PlainTextResponse(content=full_book.get_content())


@app.get("/{book}/{chapter}/{verse}")
async def as_slashes_book_chapter_verse(
    request: requests.Request,
    book: str = Query(default=..., min_length=4, max_length=20),
    chapter: int = Query(default=..., ge=0, lt=1000),
    verse: str = Query(default=..., regex=VERSE_REGEX),
    options: Options = Depends(),
):
    options.update(request)
    verse_num = validate_verses([verse])
    if verse_num != 0:
        return Response(
            content=f"Verse {verse_num} is not a verse. Accepted values include '3','15','3-19'\n",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    # Query the DB
    if "-" in verse:
        response, book = query_multiple_verses_one_chapter(
            book, chapter, verse, options
        )
    else:
        response, book = query_single_verse(book, chapter, verse, options)
    if response.is_error():
        return f"Unable to print verse. Reason {response.get_content()}"

    # Render the book with all specified options
    full_book = parse_db_response(
        result=response, user_options=options, queried_verse=f"{book} {chapter}:{verse}"
    )
    return PlainTextResponse(content=full_book.get_content())


@app.get("/{book_1}/{chapter_1}/{verse_1}/{book_2}/{chapter_2}/{verse_2}")
async def as_slashes_book1_chapter1_verse1_book2_chapter2_verse2(
    request: requests.Request,
    book_1: str = Query(default=..., min_length=4, max_length=25),
    book_2: str = Query(default=..., min_length=4, max_length=25),
    chapter_1: int = Query(default=..., le=25),
    chapter_2: int = Query(default=..., le=25),
    verse_1: str = Query(default=..., regex=VERSE_REGEX),
    verse_2: str = Query(default=..., regex=VERSE_REGEX),
    options: Options = Depends(),
):
    options.update(request)
    verse_num = validate_verses([verse_1, verse_2])
    if verse_num != 0:
        return Response(
            content=f"Verse {verse_num} is not a verse. Accepted values include '3','15','159'\n",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    # Query the DB
    response, book_1, book_2 = query_multiple_verses(
        starting_book=book_1,
        starting_chapter=chapter_1,
        starting_verse=verse_1,
        ending_book=book_2,
        ending_chapter=chapter_2,
        ending_verse=verse_2,
        options=options,
    )
    if response.is_error():
        return f"Unable to print verse. Reason {response.get_content()}"

    # Have the returned verse look nice.
    if book_1 == book_2:
        full_verse = f"{book_1} {chapter_1}:{verse_1} - {chapter_2}:{verse_2}"
    elif chapter_1 == chapter_2:
        full_verse = f"{book_1} {chapter_1}:{verse_1} - {verse_2}"
    else:
        full_verse = f"{book_1} {chapter_1}:{verse_1} - {book_2} {chapter_2}:{verse_2}"
    # Render the book with all specified options
    full_book = parse_db_response(
        result=response,
        user_options=options,
        queried_verse=full_verse,
    )
    return PlainTextResponse(content=full_book.get_content())


def validate_verses(verse_list: list) -> int:
    """
    Iterates through each verse to make sure it matches the verse regex.

    Args:
        verse_list (list): A list containing each verse passed to the method.
    Returns:
        An int indicating which verse (if any) is invalid.
            0 - All Verses valid
            1 - Verse 1 Invalid
            2 - Verse 2 Invalid
    Raises:
        None
    """
    for count, verse in enumerate(verse_list):
        if search(VERSE_REGEX, verse) is None:
            return count + 1
    else:
        return 0


def connect_to_db():
    """Connect to MySQL database"""
    conn = None

    try:
        conn = connect(
            host=DB_CONFIG["db_host"],
            database=DB_CONFIG["db_dbname"],
            user=DB_CONFIG["db_user"],
            password=DB_CONFIG["db_password"],
            port=DB_CONFIG["db_port"],
        )
        if conn.is_connected():
            return conn
    except Error as e:
        critical(f"Cannot connect to DB! Attempting to connect on localhost {e}")

    # Try to connect to localhost if regular connection fails
    try:
        conn = connect(
            host="localhost",
            database=DB_CONFIG["db_dbname"],
            user=DB_CONFIG["db_user"],
            password=DB_CONFIG["db_password"],
            port=DB_CONFIG["db_port"],
        )
        if conn.is_connected():
            return conn
    except Exception as e:
        critical(f"Cannot connect to DB! {e}")
        return None


def query_db(db_conn, db_cmd: str, parameters: tuple, options: Options) -> str:
    """
    Run the DB command and return all data.

    Args:
        db_conn:            MySQL connector object.
        db_cmd (str):       The command to run with % for commands.
        parameters(tuple):  The parameters to substute into the db_cmd
        options (Options):  The options list for the request (will support verse numbers later)
    Returns:
        ReturnObject(Status.Success, str)
            The str contains all queried fields from the DB.
    Raises:
        None
    """
    with db_conn.cursor(buffered=True) as cursor:
        try:
            if options is None or (
                options is not None and options.verse_numbers is False
            ):
                cursor.execute(db_cmd, parameters)
                if cursor.with_rows:
                    text = cursor.fetchall()
                    # Combine all returned fields into a single string.
                    return ReturnObject(
                        Status.Success, " ".join([str(verse[0]) for verse in text])
                    )
            elif options is not None and options.verse_numbers is True:
                # Ensure the verse numbers are also queried.
                db_cmd = db_cmd.replace(" t ", " t,v ")
                cursor.execute(db_cmd, parameters)
                if cursor.with_rows:
                    text = cursor.fetchall()
                    for count, verse in enumerate(text):
                        small_verse_number = ""
                        for num in str(verse[-1]):
                            """
                            Convert each verse number into the small text. This is done by
                            adding 8320 to the Unicode value of each verse number, which converts it
                            into the associated 'small' Unicode number.
                            3           --> ₃
                            chr(3)='3'      chr(8323)='₃'
                            """
                            small_verse_number += REGULAR_TO_SUPERSCRIPT[num]
                        # Update tuple (by creating new one)
                        text[count] = (verse[0], small_verse_number)
                    return ReturnObject(
                        Status.Success,
                        " ".join([verse[-1] + verse[0] for verse in text]),
                    )
        except Error as e:
            warning(f"Bible verse not found. {e}")
            return ReturnObject(Status.Failure, "Verse not found")


def set_query_bible_version(book_version: str, query_type: str) -> str:
    """
    The verse cannot be set dynamically, so this method must be used.
    """
    if book_version.lower() in ["t_asv", "asv"]:
        if query_type == "single":
            return "SELECT t from t_asv where id=%s"
        elif query_type == "range":
            return "SELECT t from t_asv where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_asv where id like %s"

    elif book_version.lower() in ["t_bbe", "bbe"]:
        if query_type == "single":
            return "SELECT t from t_bbe where id=%s"
        elif query_type == "range":
            return "SELECT t from t_bbe where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_bbe where id like %s"

    elif book_version.lower() in ["t_kjv", "kjv"]:
        if query_type == "single":
            return "SELECT t from t_kjv  where id=%s"
        elif query_type == "range":
            return "SELECT t from t_kjv where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_kjv where id like %s"

    elif book_version.lower() in ["t_web", "web"]:
        if query_type == "single":
            return "SELECT t from t_web where id=%s"
        elif query_type == "range":
            return "SELECT t from t_web where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_web where id like %s"

    elif book_version.lower() in ["t_ylt", "ylt"]:
        if query_type == "single":
            return "SELECT t from t_ylt where id=%s"
        elif query_type == "range":
            return "SELECT t from t_ylt where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_ylt where id like %s"
    else:
        return None


def bookname_to_bookid(book: str, database_connection) -> str:
    """
    Convert a book name into the ID of the book (number in bible)
    so it can be queried.
    """
    db_cmd = "SELECT b FROM key_abbreviations_english WHERE a=%s AND p=1"
    db_parameters = (book,)
    result = query_db(
        db_conn=database_connection,
        db_cmd=db_cmd,
        parameters=db_parameters,
        options=None,
    )
    if result.is_error():
        return (result.get_error(),)
    # Querying for books like 'Psalms' and 'John' returns multiple instances of the same result
    # So the first number must be pulled from the text.
    return result.get_content().split(" ")[0]


def get_full_book_name(book_id: str, book: str, database_connection):
    """
    Returns the full name of the book.

    Takes in the book_id from the previous result and then queries all
    different variations of that book name. The book with the highest
    id value (separate from the book_id) is the 'proper' name of the book.

    Args:
        Book - str
        db_conn - MySQL DB connection
    Returns:
        book_name - str
            This will be the book name the user passed in if an error occured.
            Otherwise it will be the full book name.
    Raises:
        None
    """
    db_query = (
        "SELECT a FROM key_abbreviations_english WHERE b=%s ORDER BY id DESC LIMIT 1"
    )
    db_parameters = (book_id,)
    result = query_db(
        db_conn=database_connection,
        db_cmd=db_query,
        parameters=db_parameters,
        options=None,
    )
    if result.is_error():
        return book
    return result.get_content()


def query_entire_chapter(book: str, chapter: int, options: Options) -> ReturnObject:
    """
    Take in a single verse and return the corresponding text.

    Args:
        book (str):         The book to be queried
        chapter (int):      The chapter to be queried
        options (Options):  The options list for the request (will support verse numbers later)
    Returns:
        (ReturnObject, book)
            ReturnObject(Status.success, str):Contains all queried fields from the DB.
            book (str): Contains the updated book name.
    Raises:
        None
    """
    db_conn = connect_to_db()
    if db_conn is None:
        return (ReturnObject(Status.MajorFailure, "Cannot connect to local DB"), book)

    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    if book_id == "" and not str.isnumeric(book_id):
        warning(f"Bible book not found!")
        return (ReturnObject(Status.Failure, f"Book '{book}' not found\n"), book)
    # Ensure the full name of the book is returned ('1Jo'->'1 John')
    book = get_full_book_name(book_id, book, db_conn)
    # fmt: off
    verse_id = (
        "0" * (2 - len(book_id)) + book_id +
        "0" * (3 - len(str(chapter))) + str(chapter) + 
        "%%"
    )
    # fmt: on
    db_cmd = set_query_bible_version(options.version, "chapter")
    parameters = (verse_id,)
    if db_cmd is None:
        warning(f"Cannot find bible version {verse_id}.")
        return ReturnObject(Status.Failure, "Invalid Bible Version\n")
    result = query_db(db_conn, db_cmd, parameters, options)

    if result.is_error():
        return (ReturnObject(Status.Failure, result.get_error()), book)
    try:
        return (ReturnObject(Status.Success, result.get_content()), book)
    except TypeError as te:
        warning(f"Invalid DB return {te}")
        return (
            ReturnObject(
                Status.MajorFailure,
                "Invalid return from DB, please contact site admin\n",
            ),
            book,
        )


def query_single_verse(
    book: str, chapter: int, verse: str, options: Options
) -> ReturnObject:
    """
    Take in a single verse and return the corresponding text.

    Args:
        book (str):         The book to be queried
        chapter (int):      The chapter to be queried
        verse (str):        The verse to be queried
        options (Options):  The options list for the request (will support verse numbers later)
    Returns:
        (ReturnObject, book)
            ReturnObject(Status.success, str):Contains all queried fields from the DB.
            book (str): Contains the updated book name.
    Raises:
        None
    """
    db_conn = connect_to_db()
    if db_conn is None:
        return (ReturnObject(Status.MajorFailure, "Cannot connect to local DB"), book)

    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    if book_id == "" and not str.isnumeric(book_id):
        warning(f"Bible book not found!")
        return (ReturnObject(Status.Failure, f"Book '{book}' not found\n"), book)
    # Ensure the full name of the book is returned ('1Jo'->'1 John')
    book = get_full_book_name(book_id, book, db_conn)
    # fmt: off
    verse_id = (
        "0" * (2 - len(book_id)) + book_id +
        "0" * (3 - len(str(chapter))) + str(chapter) + 
        "0" * (3 - len(verse)) + verse
    )
    # fmt: on
    db_cmd = set_query_bible_version(options.version, "single")
    parameters = (verse_id,)
    if db_cmd is None:
        warning(f"Cannot find bible version {verse_id}.")
        return (ReturnObject(Status.Failure, "Invalid Bible Version\n"), book)
    result = query_db(db_conn, db_cmd, parameters, options)

    if result.is_error():
        return (ReturnObject(Status.Failure, result.get_error()), book)
    try:
        return (ReturnObject(Status.Success, result.get_content()), book)
    except TypeError as te:
        warning(f"Invalid DB return {te}")
        return (
            ReturnObject(
                Status.MajorFailure,
                "Invalid return from DB, please contact site admin\n",
            ),
            book,
        )


def query_multiple_verses_one_chapter(
    book: str, chapter: int, verse: str, options: Options
) -> ReturnObject:
    """
    Take in a single verse and return the corresponding text.

    Args:
        book (str):         The book to be queried
        chapter (int):      The chapter to be queried
        verse (str):        The verse to be queried. In the form '{verse_1}-{verse_2}'
        options (Options):  The options list for the request (will support verse numbers later)
    Returns:
        (ReturnObject, book)
            ReturnObject(Status.success, str):Contains all queried fields from the DB.
            book (str): Contains the updated book name.
    Raises:
        None
    """
    db_conn = connect_to_db()
    if db_conn is None:
        return (ReturnObject(Status.MajorFailure, "Cannot connect to local DB"), book)
    if len(verse.split("-")) != 2:
        return (
            ReturnObject(
                Status.Failure,
                f"Invalid Verse! {verse} Cannot be split up into two parts!",
            ),
            book,
        )
    starting_verse, ending_verse = verse.split("-")
    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    if book_id == "" and not str.isnumeric(book_id):
        warning(f"Bible book not found!")
        return (ReturnObject(Status.Failure, f"Book '{book}' not found\n"), book)

    # Ensure the full name of the book is returned ('1Jo'->'1 John')
    book = get_full_book_name(book_id, book, db_conn)
    # fmt: off
    starting_verse_id = (
        "0" * (2 - len(book_id)) + book_id +
        "0" * (3 - len(str(chapter))) + str(chapter) + 
        "0" * (3 - len(starting_verse)) + starting_verse
    )
    ending_verse_id = (
        "0" * (2 - len(book_id)) + book_id +
        "0" * (3 - len(str(chapter))) + str(chapter) + 
        "0" * (3 - len(ending_verse)) + ending_verse
    )
    # fmt: on
    db_cmd = set_query_bible_version(options.version, "range")
    parameters = (starting_verse_id, ending_verse_id)
    if db_cmd is None:
        warning(f"Cannot find bible version {starting_verse} {ending_verse}.")
        return (ReturnObject(Status.Failure, "Invalid Bible Version\n"), book)
    result = query_db(db_conn, db_cmd, parameters, options)

    if result.is_error():
        return (ReturnObject(Status.Failure, result.get_error()), book)
    try:
        return (ReturnObject(Status.Success, result.get_content()), book)
    except TypeError as te:
        warning(f"Invalid DB return {te}")
        return (
            ReturnObject(
                Status.MajorFailure,
                "Invalid return from DB, please contact site admin\n",
            ),
            book,
        )


def query_multiple_verses(
    starting_book: str,
    starting_chapter: int,
    starting_verse: str,
    ending_book: str,
    ending_chapter: int,
    ending_verse: str,
    options: Options,
) -> ReturnObject:
    """
    Take in multiple verses and return the corresponding text.

    Args:
        starting_book (str):    The starting book to be queried
        starting_chapter (int): The starting chapter to be queried
        starting_verse (str):   The starting verse to be queried
        ending_book (str):      The ending book to be queried
        ending_chapter (int):   The ending chapter to be queried
        ending_verse (str):     The ending verse to be queried
        options (Options):      The options list for the request (will support verse numbers later)
    Returns:
        (ReturnObject, starting_book, ending_book)
            ReturnObject(Status.success, str):Contains all queried fields from the DB.
            starting_book (str): Contains the updated name of the first book.
            ending_book (str): Contains the updated name of the second book.
    Raises:
        None
    """
    db_conn = connect_to_db()
    if db_conn is None:
        return (
            ReturnObject(Status.MajorFailure, "Cannot connect to local DB"),
            starting_book,
            ending_book,
        )

    # Correlate book name to book id
    starting_book_id = bookname_to_bookid(starting_book, db_conn)
    ending_book_id = bookname_to_bookid(ending_book, db_conn)
    if (
        starting_book_id == ""
        and not str.isnumeric(starting_book_id)
        or ending_book_id == ""
        and not str.isnumeric(ending_book_id)
    ):
        warning(f"Bible book not found!")
        return (
            ReturnObject(
                Status.Failure,
                f"Books '{starting_book}' or '{ending_book}' not found\n",
            ),
            starting_book,
            ending_book,
        )
    # Ensure the full name of the book is returned ('1Jo'->'1 John')
    starting_book = get_full_book_name(
        book_id=starting_book_id, book=starting_book, database_connection=db_conn
    )
    ending_book = get_full_book_name(
        book_id=ending_book_id, book=ending_book, database_connection=db_conn
    )
    # fmt: off
    starting_verse_id = "0" * (2 - len(str(starting_book_id))) + str(starting_book_id) + \
        "0" * (3 - len(str(starting_chapter))) + str(starting_chapter) + \
        "0" * (3 - len(starting_verse)) + starting_verse

    ending_verse_id = "0" * (2 - len(str(ending_book_id))) + str(ending_book_id) + \
        "0" * (3 - len(str(ending_chapter))) + str(ending_chapter) + \
        "0" * (3 - len(ending_verse)) + ending_verse
    # fmt: on
    db_cmd = set_query_bible_version(options.version, "range")
    parameters = (starting_verse_id, ending_verse_id)
    if db_cmd is None:
        warning(f"Cannot find bible version {starting_book_id} {ending_book_id}.")
        return (
            ReturnObject(Status.Failure, "Invalid Bible Version\n"),
            starting_book,
            ending_book,
        )
    result = query_db(db_conn, db_cmd, parameters, options)

    if result.is_error():
        return (
            ReturnObject(Status.Failure, result.get_error()),
            starting_book,
            ending_book,
        )
    try:
        return (
            ReturnObject(Status.Success, result.get_content()),
            starting_book,
            ending_book,
        )
    except TypeError as te:
        warning(f"Invalid DB return {te}")
        return (
            ReturnObject(
                Status.MajorFailure,
                "Invalid return from DB, please contact site admin\n",
            ),
            starting_book,
            ending_book,
        )


def parse_db_response(
    result: ReturnObject, user_options: Options, queried_verse: dict
) -> tuple:
    """
    After querying the DB and getting a ResponseObject, this method parses it into a
    proper response for FastAPI.
    Does not parse the response as a book if 'text'/'t' = yes
    This returns a tuple that can be returned to the client.
    The color formatting will also be done here.
    """

    if result.is_error():
        return result
    if result.get_content() == "":
        return ReturnObject(status=Status.Failure, content="Verse not found!")
    if user_options.text_only:
        # Add newline character at end of returned text
        return ReturnObject(
            status=result.get_status, content=result.get_content() + "\n"
        )

    return create_book(
        bible_verse=result.get_content(),
        user_options=user_options,
        request_verse=queried_verse,
    )
