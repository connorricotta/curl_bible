# Bible Webapp
# Query the Holy Bible using curl
# Author: CR

# Supports the following versions:
#   - King James Version (KJV)
#   - American Standard-ASV1901 (ASV)
#   - Bible in Basic English (BBE)
#   - World English Bible (WEB)
#   - Young's Literal Translatiobible.sh/book=John&verse=3&verse=15,17,19:20n (YLT)

# Imports
import math
import textwrap
from flask import Flask, request
from mysql.connector import Error, connect
from enum import Enum
from mysql.connector.connection_cext import CMySQLConnection
from yaml import safe_load
from os import path
from sys import exit
import logging
from book_config import Book, Options
from werkzeug.datastructures import ImmutableMultiDict

# Global Vars
app = Flask(__name__)
config = {}


class Query(Enum):
    Single = 0
    Multiple = 1


class Status(Enum):
    Success = 0
    Failure = 401
    MajorFailure = 501


class ReturnObject():
    def __init__(self, status: int, content: str) -> None:
        self.status = status
        self.content = content

    def get_content(self):
        return self.content

    def get_error(self):
        return self.status

    def is_error(self):
        # Define an error status as having a value of 1
        # Otherwise, return success
        return self.status % 2 == 1


@app.route("/", methods=["POST", "GET"])
def argument_query():
    # Check for arguments version
    options = parse_options(request.args)

    if "book" in request.args and "chapter" in request.args and "verse" in request.args:
        book = request.args['book']
        chapter = request.args['chapter']
        verse = request.args['verse']

        if not are_args_valid(book, chapter, verse):
            return ("Invalid arguments\n", 400)

        # Check for multiple quotes. This function only does quotes from the
        # same chapter.
        if '-' in verse:
            return parse_db_response(
                query_multiple_verses_one_book(
                    book, chapter, verse, request.args, options), options)

        return parse_db_response(
            query_single_verse(
                book,
                chapter,
                verse,
                request.args,
                options), options)

    elif "book" in request.args and "chapter" in request.args:
        book = request.args['book']
        chapter = request.args['chapter']
        if not are_args_valid(book, chapter):
            return ("Invalid arguments", 400)
        return parse_db_response(
            query_entire_chapter(
                book,
                chapter,
                request.args,
                options), options)
    logging.exception("Unknown error")
    return ("Unknown error", 400)


@app.route('/<full_verse>')
def full_query(full_verse):
    try:
        parts = full_verse.split(":")
        options = parse_options(request.args)

        if len(parts) == 3:
            [book, chapter, verse] = parts

            # Check for a range of verses
            if '-' in verse:
                if not are_args_valid(book, chapter, verse):
                    return ("Invalid arguments", 400)
                return parse_db_response(
                    query_multiple_verses_one_book(
                        book, chapter, verse, request.args, options), options, [book, chapter, verse])

        # Check for an entire chapter
        elif len(parts) == 2:
            [book, chapter] = parts
            return parse_db_response(
                query_entire_chapter(
                    book, chapter, request.args, options), options, [book, chapter])

        # Check for multiple chapters
        elif len(parts) >= 6:
            [starting_book, starting_chapter, starting_verse,
                ending_book, ending_chapter, ending_verse] = parts

            return parse_db_response(
                query_multiple_chapters(starting_book, starting_chapter, starting_verse,
                                        ending_book, ending_chapter, ending_verse, request.args, options), options,
                [starting_book, starting_chapter, starting_verse, ending_book, ending_chapter, ending_verse])

        # Otherwise, check for a single chapter
        if not are_args_valid(book, chapter, verse):
            return ("Invalid arguments", 400)
        return parse_db_response(query_single_verse(
            book, chapter, verse, request.args, options
        ), options, [book, chapter, verse])

    except Exception as e:
        logging.exception(f"Uncaught error {e}")
        return ("Invalid verse", 400)


@app.route('/<book>/<chapter>/<verse>')
def slash_query_full(book, chapter, verse):
    '''
    Parse queries like:
        - /John/3/15
        - /John/3/15-19
    '''
    if not are_args_valid(book, chapter, verse):
        return ("Invalid arguments", 400)
    options = parse_options(request.args)
    if '-' in verse:
        return parse_db_response(
            query_multiple_verses_one_book(
                book, chapter, verse, request.args, options), options, [book, chapter, verse])
    return parse_db_response(
        query_single_verse(
            book,
            chapter,
            verse,
            request.args,
            options), options, [book, chapter, verse])


@app.route('/<book>/<chapter>')
def slash_query_part(book, chapter):
    options = parse_options(request.args)
    if not are_args_valid(book, chapter):
        return ("Invalid arguments", 400)
    return parse_db_response(
        query_entire_chapter(
            book,
            chapter,
            request.args,
            options), options, [book, chapter])


@app.route('/versions')
def show_bible_versions():
    '''
    Just return a list of the bibles supported by this webapp.
    Taken from the 'bible_version_key' table in the DB.
    '''
    return ('''
    All current supported versions of the Bible.
    Use the value in 'Version Name' to use that version of the bible, such as:
        curl -L "bible.sh/John:3:15?version=BBE"

    ╭──────────────┬──────────┬─────────────────────────────┬───────────────╮
    │ Version Name │ Language │ Name of version             │ Copyright     │
    ├──────────────┼──────────┼─────────────────────────────┼───────────────┤
    │     ASV      │ English  │ American Standard (ASV1901) │ Public Domain │
    │     BBE      │ English  │ Bible in Basic English      │ Public Domain │
    │     KJV      │ English  │ King James Version          │ Public Domain │
    │     WEB      │ English  │ World English Bible         │ Public Domain │
    │     YLT      │ English  │ Young's Literal Translation │ Public Domain │
    ╰──────────────┴──────────┴─────────────────────────────┴───────────────╯
    ''', 200)


@app.route('/book_render')
def render_book():
    '''
    start                middle                 end
    |                    |                     |
    V                    V                     V
        ___________________ ___________________
    .-/|                   ⋁                   |\\-. <─ top
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   |||| <─ middle
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||__________________ │ __________________|||| <─ bottom_single_pg
    ||/===================\\│/===================\\|| <─ bottom_multi_pg
    `--------------------~___~--------------------𝅪 <─ bottom_final_pg
    This book is rendered using static parts (mostly the corners and the middle)
    and the rest is generated dynamically based on the parameters passed in.
    '''
    if 'length' in request.args and str.isnumeric(request.args['length']) and \
            'width' in request.args and str.isnumeric(request.args['width']):
        width = int(request.args['width'])
        length = int(request.args['length'])
    else:
        width = 40
        length = 20

    book = Book()
    book_parts = book.get_book_parts()
    # I know this looks strange, but it allows for code re-use.
    page_length = width // 2
    final_book_top = "    " + book_parts['top_level'] * page_length + " " + book_parts['top_level'] * page_length + \
        "    \n" + book_parts['top_start'] + " " * (page_length - 1) + book_parts['top_middle'] + " " * (page_length - 1) + \
        book_parts['top_end']

    final_book_middle = (book_parts['middle_start'] + " " * (page_length - 1) + book_parts['middle'] +
                         " " * (page_length - 1) + book_parts['middle_end'] + "\n") * length

    final_bottom_single_pg = book_parts['bottom_single_pg_start'] + book_parts['top_level'] * (page_length - 1) + \
        book_parts['bottom_single_pg_middle'] + book_parts['top_level'] * (page_length - 1) + \
        book_parts['bottom_single_pg_end'] + "\n"

    final_bottom_multi_pg = book_parts['bottom_multi_pg_left'] + "=" * (page_length - 1) + \
        book_parts['bottom_multi_pg_middle'] + "=" * \
        (page_length - 1) + \
        book_parts['bottom_multi_pg_end'] + "\n"

    final_bottom_final_pg = book_parts['bottom_final_pg_left'] + "-" * (page_length - 2) + \
        book_parts['bottom_final_pg_middle'] + "-" * \
        (page_length - 2) + \
        book_parts["bottom_final_pg_end"] + "\n"

    return (final_book_top + final_book_middle + final_bottom_single_pg +
            final_bottom_multi_pg + final_bottom_final_pg, 200)


@app.before_first_request
def config():
    '''
    1. Read in the configuration file in order to connect to the database on app start-up.
    2. Enable logging
    '''
    global config
    if not path.exists('config/config.yaml'):
        logging.critical(
            "Cannot load DB config file, check README in GitHub repo")
        exit(1)
    with open('config/config.yaml') as f:
        config = safe_load(f)

    logging.basicConfig(
        filename='bible.log',
        filemode='a',
        format='%(asctime)s | Level:%(levelname)s | Logger:%(name)s | Src:%(filename)s.%(funcName)s@%(lineno)d | Msg:%(message)s',
        datefmt='%m/%d/%y %I:%M:%S %p %z (%Z)')


def connect_to_db() -> CMySQLConnection:
    """ Connect to MySQL database """
    conn = None

    try:
        conn = connect(
            host=config['db']['host'],
            database=config['db']['database'],
            user=config['db']['user'],
            password=config['db']['password'],
            port=config['db']['port']
        )

        if conn.is_connected():
            return conn

    except Error as e:
        logging.critical(f"Cannot connect to DB! {e}")
        return None


def parse_options(options: ImmutableMultiDict):
    if options is None:
        return None
    if 'o' in options:
        return Options(options['o']).get_options_dict()
    elif 'options' in options:
        return Options(options['options']).get_options_dict()


def set_query_bible_version(book_version: str, query_type: str) -> str:
    '''
    The verse cannot be set dynamically, so this method must be used.
    '''
    if book_version in ["t_asv", "ASV"]:
        if query_type == "single":
            return "SELECT t from t_asv where id=%s"
        elif query_type == "range":
            return "SELECT t from t_asv where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_asv where id like %s"

    elif book_version in ["t_bbe", "BBE"]:
        if query_type == "single":
            return "SELECT t from t_bbe where id=%s"
        elif query_type == "range":
            return "SELECT t from t_bbe where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_bbe where id like %s"

    elif book_version in ["t_jkv", "JVK"]:
        if query_type == "single":
            return "SELECT t from t_jvk where id=%s"
        elif query_type == "range":
            return "SELECT t from t_jvk where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_jvk where id like %s"

    elif book_version in ["t_web", "WEB"]:
        if query_type == "single":
            return "SELECT t from t_web where id=%s"
        elif query_type == "range":
            return "SELECT t from t_web where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_web where id like %s"

    elif book_version in ["t_ylt", "YLT"]:
        if query_type == "single":
            return "SELECT t from t_ylt where id=%s"
        elif query_type == "range":
            return "SELECT t from t_ylt where id between %s and %s"
        elif query_type == "chapter":
            return "SELECT t from t_ylt where id like %s"
    else:
        return None


def bookname_to_bookid(
        book: str,
        database_connection: CMySQLConnection) -> str:
    '''
    Convert a book name into the ID of the book (number in bible)
    so it can be queried.
    '''
    db_cmd = "SELECT b from key_abbreviations_english where a=%s and p=1"
    db_parameters = (book,)
    result = query_db(
        db_conn=database_connection,
        db_cmd=db_cmd,
        parameters=db_parameters
    )
    if result.is_error():
        return (result.get_error(),)
    # Querying for books like 'Psalms' and 'John' returns multiple instances of the same result
    # So the first number must be pulled from the text.
    return result.get_content().split(" ")[0]


def query_single_verse(
        book: str,
        chapter: str,
        verse: str,
        args: ImmutableMultiDict,
        options: dict) -> ReturnObject:
    db_conn = connect_to_db()
    if db_conn is None:
        return ReturnObject(Status.Failure.value, "Cannot connect to local DB")

    # Set a default version if none is specified
    if "version" in args:
        bible_version = args['version']
    elif options is not None and "version" in options:
        bible_version = options['version']
    else:
        bible_version = "t_asv"

    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    try:
        assert book_id is not None and str.isnumeric(book_id)
    except AssertionError as ae:
        logging.warning(f"Bible book not found! {ae}")
        return ReturnObject(Status.Failure, f"Book '{book}' not found\n")

    verse_id = "0" * (2 - len(book_id)) + book_id + "0" * \
        (3 - len(chapter)) + chapter + "0" * (3 - len(verse)) + verse

    db_cmd = set_query_bible_version(bible_version, "single")
    parameters = (verse_id,)
    if db_cmd is None:
        logging.warning(f"Cannot find bible version {verse_id}.")
        return ReturnObject(Status.Failure.value, "Invalid Bible Version")
    result = query_db(db_conn, db_cmd, parameters)

    if result.is_error():
        return ReturnObject(Status.Failure.value, result.get_error())
    try:
        return ReturnObject(Status.Success.value, result.get_content())
    except TypeError as te:
        logging.warning(f"Invalid DB return {te}")
        return ReturnObject(
            Status.MajorFailure,
            "Invalid return from DB, please contact site admin")


def query_multiple_verses_one_book(
        book: str,
        chapter: str,
        verse: str,
        args: ImmutableMultiDict,
        options: dict) -> ReturnObject:
    db_conn = connect_to_db()
    if db_conn is None:
        return ReturnObject(
            Status.MajorFailure,
            "Cannot connect to local DB, please contact site admin.")

    # Set a default version if none is specified
    if "version" in args:
        bible_version = args['version']
    elif options is not None and "version" in options:
        bible_version = options['version']
    else:
        bible_version = "t_asv"

    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    try:
        assert book_id is not None and str.isnumeric(book_id)
    except AssertionError as ae:
        logging.warning(f"Bible book not found! {ae}")
        return ReturnObject(Status.Failure.value, f"Book '{book}' not found\n")

    # Pull out the starting and ending verse
    [starting_verse, ending_verse] = verse.split("-")
    # Make sure that the verses are valid
    if not str.isnumeric(starting_verse) or not str.isnumeric(ending_verse):
        return ReturnObject(Status.Failure, f"Invalid Verse {verse}\n")
    if int(ending_verse) < int(starting_verse):
        return ReturnObject(
            Status.Failure,
            f"Starting Verse ({ending_verse}) must be greater than Ending Verse ({starting_verse})\n")

    starting_verse_id = "0" * (2 - len(book_id)) + book_id + \
        "0" * (3 - len(chapter)) + chapter + \
        "0" * (3 - len(starting_verse)) + starting_verse

    ending_verse_id = "0" * (2 - len(book_id)) + book_id + \
        "0" * (3 - len(chapter)) + chapter + \
        "0" * (3 - len(ending_verse)) + ending_verse

    db_cmd = set_query_bible_version(bible_version, "range")
    if db_cmd is None:
        return ReturnObject(Status.Failure.value, "Invalid Bible Version")
    parameters = (starting_verse_id, ending_verse_id)

    result = query_db(db_conn, db_cmd, parameters)

    if result.is_error():
        return ReturnObject(Status.Failure, result.get_error())
    if result.get_content() == '':
        return ReturnObject(Status.Failure, f"Verse not found!\n")
    return result


def query_entire_chapter(book: str, chapter: str, args: ImmutableMultiDict,
                         options: dict):
    db_conn = connect_to_db()
    if db_conn is None:
        return ReturnObject(
            Status.MajorFailure,
            "Cannot connect to local DB, please contact site admin.")

    # Set a default version if none is specified
    if "version" in args:
        bible_version = args['version']
    elif options is not None and "version" in options:
        bible_version = options['version']
    else:
        bible_version = "t_asv"

    # Correlate book name to book id
    book_id = bookname_to_bookid(book, db_conn)
    try:
        assert book_id is not None and str.isnumeric(book_id)
    except AssertionError as ae:
        logging.warning(f"Bible book not found! {ae}")
        return ReturnObject(Status.Failure.value, f"Book '{book}' not found\n")

    # %% is the escaped wildcard '%' in mysql.
    entire_verse = "0" * (2 - len(book_id)) + book_id + \
        "0" * (3 - len(chapter)) + chapter + "%%"

    db_cmd = set_query_bible_version(bible_version, "chapter")
    if db_cmd is None:
        return ReturnObject(Status.Failure.value, "Invalid Bible Version")
    parameters = (entire_verse,)

    result = query_db(db_conn, db_cmd, parameters)

    if result.is_error():
        return ReturnObject(Status.Failure, result.get_error())
    if result.get_content() == '':
        return ReturnObject(Status.Failure, f"Verse not found!\n")
    return result


def query_multiple_chapters(starting_book: str, starting_chapter: str,
                            starting_verse: str, ending_book: str, ending_chapter: str, ending_verse: str, args: ImmutableMultiDict,
                            options: dict):
    db_conn = connect_to_db()
    if db_conn is None:
        return ReturnObject(
            Status.MajorFailure,
            "Cannot connect to local DB, please contact site admin.")

    # Set a default version if none is specified
    if "version" in args:
        bible_version = args['version']
    elif options is not None and "version" in options:
        bible_version = options['version']
    else:
        bible_version = "t_asv"

    # Correlate book name to book id
    starting_book_id = bookname_to_bookid(starting_book, db_conn)
    ending_book_id = bookname_to_bookid(ending_book, db_conn)
    try:
        assert starting_book_id is not None and str.isnumeric(starting_book_id)
        assert ending_book_id is not None and str.isnumeric(ending_book_id)
    except AssertionError as ae:
        logging.warning(f"Bible book not found! {ae}")
        return ReturnObject(
            Status.Failure.value, f"Book '{starting_book_id} {ending_book_id}' not found\n")

    starting_verse_id = "0" * (2 - len(starting_book_id)) + starting_book_id + \
        "0" * (3 - len(starting_chapter)) + starting_chapter + \
        "0" * (3 - len(starting_verse)) + starting_verse

    ending_verse_id = "0" * (2 - len(ending_book_id)) + ending_book_id + \
        "0" * (3 - len(ending_chapter)) + ending_chapter + \
        "0" * (3 - len(ending_verse)) + ending_verse

    db_cmd = set_query_bible_version(bible_version, "range")
    if db_cmd is None:
        return ReturnObject(Status.Failure.value, "Invalid Bible Version")
    parameters = (starting_verse_id, ending_verse_id)

    result = query_db(db_conn, db_cmd, parameters)

    if result.is_error():
        return ReturnObject(Status.Failure, result.get_error())
    if result.get_content() == '':
        return ReturnObject(Status.Failure, f"Verse not found!\n")
    return result


def query_db(db_conn: CMySQLConnection, db_cmd: str, parameters: tuple):
    with db_conn.cursor(buffered=True) as cursor:
        try:
            cursor.execute(db_cmd, parameters)
            if cursor.with_rows:
                text = cursor.fetchall()
                # Combine all returned fields into a single string.
                return ReturnObject(Status.Success.value,
                                    ' '.join([str(verse[0]) for verse in text]))
        except Error as e:
            logging.warning(f"Bible verse not found. {e}")
            return ReturnObject(Status.Failure.value, "Verse not found")


def parse_db_response(result: ReturnObject, options: dict,
                      queried_verse: dict) -> tuple:
    '''
    After querying the DB and getting a ResponseObject, this method parses it into a
    proper response for Flask.
    This returns a tuple that can be returned to the client.
    The color formatting will also be done here.
    '''

    if result.get_error() == Status.Failure.value:
        return (result.get_content(), 400)
    elif result.get_error() == Status.MajorFailure.value:
        return (result.get_content(), 500)
    if result.get_content() == '':
        return (f"Verse not found!\n", 400)

    if options is not None and options['text_only'] == True:
        return (result.get_content() + "\n", 200)

    output = create_book(result.content, options, queried_verse)
    if output.is_error():
        return (output.get_content(), 400)
    else:
        return (output.get_content()[0], 200)


def are_args_valid(book: str, chapter: str, verse='0') -> bool:
    '''
    Returns True if the arguments are valid.
    The default value of '0' is passed when queries with only books and chapters
    are included.
    Make sure the arguments passed in to the command are valid. This includes
        1. Book is made of ascii characters.
        2. Verse is numeric and is equal to 176 or less (highest verse that appears in the bible)
        3. Chapter is numeric and is equal to 150 or less (highest chapter that appears in the bible)
        4. If verse is made of parts, each part is numeric and equal to 176 or less
    '''
    if verse != '0' and '-' in verse:
        [starting_verse, ending_verse] = verse.split("-")
        # Make sure that each verse is a number and less than 177.
        if (not str.isnumeric(starting_verse) or not str.isnumeric(ending_verse)) or \
            (str.isnumeric(starting_verse) and int(starting_verse) > 176) or \
                (str.isnumeric(ending_verse) and int(ending_verse) > 176):
            return False
        elif (str.isascii(book)):
            return True

    if (str.isnumeric(verse) and int(verse) <= 176 and
        str.isnumeric(chapter) and int(chapter) <= 150 and
            str.isascii(book)):
        return True
    return False


def create_book(bible_verse: str, options: ImmutableMultiDict,
                request_verse: dict):
    '''
    start                middle                 end
    |                    |                     |
    V                    V                     V
        ___________________ ___________________
    .-/|                   ⋁                   |\\-. <─ top
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   |||| <─ middle
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||                   │                   ||||
    ||||__________________ │ __________________|||| <─ bottom_single_pg
    ||/===================\\│/===================\\|| <─ bottom_multi_pg
    `--------------------~___~--------------------𝅪 <─ bottom_final_pg
    This book is rendered using static parts (mostly the corners and the middle)
    and the rest is generated dynamically based on the parameters passed in.
    '''
    book = Book()

    if options is not None:
        if 'length' in options and options['length'] > 0:
            length = options['length']
        else:
            return ReturnObject(Status.Failure.value, "Invalid length\n")

        # Width is the total area of the text, so it must be split in half
        # (one for each side). Then 2 is taken to provide a space on each side.
        if 'width' in options and options['width'] // 2 > 2:
            width = options['width']
            splitter = textwrap.TextWrapper(width=(options['width'] // 2 - 2))
        else:
            return ReturnObject(Status.Failure.value, "Invalid Width\n")

        if options['text_color'] == False:
            book_parts = book.get_no_color()
        else:
            book_parts = book.get_color()

    else:
        width = 80
        length = 20
        splitter = textwrap.TextWrapper(width=38)
        book_parts = book.get_color()

    formatted_text = splitter.wrap(bible_verse)
    final_book_middle_array = []
    page_width = width // 2
    # Add three lines to the start of the verses
    if len(request_verse) == 3:
        formatted_verse = f"{request_verse[0]} {request_verse[1]}:{request_verse[2]}"
    elif len(request_verse) == 6:
        formatted_verse = f"{request_verse[0]} {request_verse[1]}:{request_verse[2]}-{request_verse[3]} {request_verse[4]}:{request_verse[5]} "
    else:
        formatted_verse = ' '.join(request_verse)
    spaced_verse = (page_width - len(formatted_verse)) // 2
    formatted_text.insert(0, "")
    formatted_text.insert(0, " " * spaced_verse +
                          formatted_verse + " " * (spaced_verse - 1))
    formatted_text.insert(0, "")

    # Generating the book in this way allows for the easy modification of
    # book generation.
    final_book_top = "    " + book_parts['top_level'] * page_width + " " + book_parts['top_level'] * page_width + \
        "    \n" + book_parts['top_start'] + " " * (page_width - 1) + book_parts['top_middle'] + " " * (page_width - 1) + \
        book_parts['top_end']

    for i in range((length // 2)):
        try:
            if i < len(formatted_text):
                text = formatted_text[i]
                second_text_index = math.ceil(length / 2) + i

            if (i == (length // 2 - 1)):
                if len(formatted_text[second_text_index]) >= page_width - 3:
                    formatted_text[second_text_index] = formatted_text[second_text_index][:-3] + "..."
                else:
                    formatted_text[second_text_index] += "..."
            # If too big for second text, only display the first
            if i < len(formatted_text) and second_text_index >= len(
                    formatted_text):
                final_book_middle_array.append(
                    book_parts['middle_start'] +
                    f" {text}" + " " * (page_width - (len(text) + 1)) +
                    book_parts['middle'] +
                    " " * (page_width) +
                    book_parts['middle_end'] + "\n")  # nopep8
            # If too big for first, don't display any text
            elif i >= len(formatted_text):
                final_book_middle_array.append(
                    book_parts['middle_start'] +
                    " " * (page_width) +
                    book_parts['middle'] +
                    " " * (page_width) +
                    book_parts['middle_end'] + "\n")  # nopep8
            # Display text regularly
            else:
                final_book_middle_array.append(
                    book_parts['middle_start'] +
                    f" {text}" + " " * (page_width - (len(text) + 1)) +
                    book_parts['middle'] +
                    f" {formatted_text[second_text_index]}" + " " * (page_width - (len(formatted_text[second_text_index]) + 1)) +
                    book_parts['middle_end'] + "\n")  # nopep8

        except Exception as e:
            logging.exception(e)
            continue

    final_bottom_single_pg = book_parts['bottom_single_pg_start'] + book_parts['top_level'] * (page_width - 1) + \
        book_parts['bottom_single_pg_middle'] + book_parts['top_level'] * (page_width - 1) + \
        book_parts['bottom_single_pg_end'] + "\n"

    final_bottom_multi_pg = book_parts['bottom_multi_pg_left'] + "=" * (page_width - 1) + \
        book_parts['bottom_multi_pg_middle'] + "=" * \
        (page_width - 1) + \
        book_parts['bottom_multi_pg_end'] + "\n"

    final_bottom_final_pg = book_parts['bottom_final_pg_left'] + "-" * (page_width - 2) + \
        book_parts['bottom_final_pg_middle'] + "-" * \
        (page_width - 2) + \
        book_parts["bottom_final_pg_end"] + "\n"

    return ReturnObject(Status.Success.value, (final_book_top + ''.join(final_book_middle_array) + final_bottom_single_pg +
                                               final_bottom_multi_pg + final_bottom_final_pg, 200))


if __name__ == "__main__":
    app.run()
