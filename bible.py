# Bible Webapp
# Query the Holy Bible using curl
# Author: CR

# Supports the following versions:
#   - King James Version (KJV)
#   - American Standard-ASV1901 (ASV)
#   - Bible in Basic English (BBE)
#   - World English Bible (WEB)
#   - Young's Literal Translation (YLT)

from http.client import REQUESTED_RANGE_NOT_SATISFIABLE
from flask import Flask, request
import mysql.connector
from mysql.connector import Error
import enum
from mysql.connector.connection_cext import CMySQLConnection

app = Flask(__name__)

class Query(enum.Enum):
    Single=0
    Multiple=1
    
class Status(enum.Enum):
    Success = 0
    Failure = 1

class ReturnObject():
    def __init__(self, status:int, content:str) -> None:
        self.status = status
        self.content = content
    
    def get_content(self):
        return self.content

    def get_error(self):
        return self.error

    def is_error(self):
    # Define an error status as having a value of 1
    # Otherwise, return success
        return self.status % 2 == 1


@app.route("/",methods=["POST","GET"])
def bible():
    # Check for arguments version
    if "book" in request.args and "chapter" in request.args and "verse" in request.args:
        # result = query_single_verse()
        book = request.args['book']
        chapter = request.args['chapter']
        verse = request.args['verse']

        db_conn = connect_to_db()
        if db_conn is None:
            return ("Cannot connect to local Database", 500)

        # Set a default version if none is specified
        if "version" in request.args:
            bible_version = request.args['version']
        else:
            bible_version = "t_asv"

        # Correlate book name to book id        
        book_id = book_to_id(book, db_conn)
        try:
            assert book_id is not None and str.isnumeric(book_id)
        except TypeError as te:
            return ("Book not found", 400)
        except AssertionError as ae:
            return ("Invalid return from DB, please contact site admin", 500)


        # Check for multiple quotes
        # This function only does quotes from the same chapter. 
        if '-' in verse:
            [starting_verse, ending_verse] = verse.split("-")
            # Make sure that the verses are valid
            if not str.isnumeric(starting_verse) or not str.isnumeric(ending_verse):
                return (f"Invalid Verse {verse}\n", 400)
            starting_verse_id = "0"*(2-len(book_id))+book_id + \
                            "0"*(3-len(chapter))+chapter + \
                            "0"*(3-len(starting_verse))+starting_verse

            ending_verse_id = "0"*(2-len(book_id))+book_id + \
                            "0"*(3-len(chapter))+chapter + \
                            "0"*(3-len(ending_verse))+ending_verse
            result = query_multiple_verses(starting_verse_id, ending_verse_id, db_conn, bible_version)
            if result.is_error():
                return (result.get_error, 400)
            return result.get_content()+"\n"
            

        result = query_single_verse(book, chapter, verse)
        if result.is_error():
            # TODO add difference between 400 and 500 errors
            return (result.get_error(), 400)
        return (result.get_content(), 200)

       

    return ("Error", 400)
   

# @app.route('/<book>/<chapter>/<verse>')
# def bible_thing(book, chapter, verse):
#     db_conn = connect_to_db()
#     book_id = book_to_id(book, db_conn)
#     if book_id is not None and isinstance(book_id, int):
#         return query_single_quote(str(book_id), chapter, verse, db_conn, True) + "\n"


def connect_to_db() -> CMySQLConnection:
    """ Connect to MySQL database """
    conn = None
    
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='bible',
            user='root',
            password='secret',
            port='33060')

        if conn.is_connected():
            return conn

    except Error as e:
        # TODO add logging
        return None


def set_single_verse_bible_version(book_version:str) -> str:
# Cannot passed in book_version, must be done manually to prevent SQL injection
    if book_version == "t_asv":
        return "SELECT t from t_asv where id=%s"
    elif book_version == "t_bbe":
        return "SELECT t from t_bbe where id=%s"
    elif book_version == "t_kjv":
        return "SELECT t from t_kjv where id=%s"
    elif book_version == "t_web":
        return "SELECT t from t_web where id=%s"
    elif book_version == "t_ylt":
        return "SELECT t from t_ylt where id=%s"
    else:
        return None


def set_multiple_verse_bible_version(book_version:str) -> str:
    if book_version == "t_asv":
        return "SELECT t from t_asv where id between %s and %s"
    elif book_version == "t_bbe":
        return "SELECT t from t_bbe where id between %s and %s"
    elif book_version == "t_kjv":
        return "SELECT t from t_kjv where id between %s and %s"
    elif book_version == "t_web":
        return "SELECT t from t_web where id between %s and %s"
    elif book_version == "t_ylt":
        return "SELECT t from t_ylt where id between %s and %s"
    else:
        return None
    

def book_to_id(book:str, database_connection: CMySQLConnection) -> str:
    db_cmd = "SELECT b from key_abbreviations_english where a=%s"
    db_parameters = (book,)
    result = query_db(
        db_conn=database_connection, 
        db_cmd=db_cmd,
        parameters=db_parameters
    )
    if result.is_error():
        return (result.get_error(),)
    return result.get_content()
   

def query_single_verse(book:str, chapter:str, verse:str) -> ReturnObject:
    db_conn = connect_to_db()
    if db_conn is None:
        return ReturnObject(Status.Failure.value, "Cannot connect to local DB")

    # Set a default version if none is specified
    if "version" in request.args:
        bible_version = request.args['version']
    else:
        bible_version = "t_asv"

    # Correlate book name to book id        
    book_id = book_to_id(book, db_conn)
    try:
        assert book_id is not None and str.isnumeric(book_id)
    except TypeError as te:
        return ReturnObject(Status.Failure, "Book not found")
    except AssertionError as ae:
        return ReturnObject(Status.Failure, "Invalid return from DB, please contact site admin")

    verse_id = "0"*(2-len(book_id))+book_id + "0"*(3-len(chapter))+chapter + "0"*(3-len(verse))+verse

    db_cmd = set_single_verse_bible_version(bible_version)
    parameters = (verse_id,)
    if db_cmd is None:
        # TODO log invalid bible version
        return ReturnObject(Status.Failure.value,"Invalid Bible Version")
    result = query_db(db_conn, db_cmd, parameters)

    if result.is_error():
        return ReturnObject(Status.Failure.value, result.get_error())
    try:
        return ReturnObject(Status.Success.value, result.get_content()+"\n")
    except TypeError as te:
        return ReturnObject(Status.Failure, "Invalid return from DB, please contact site admin")
    

def query_multiple_verses(starting_verse_id:str, ending_verse_id, db_conn:CMySQLConnection, book_version:str) -> ReturnObject: 
    db_cmd = set_multiple_verse_bible_version(book_version)
    if db_cmd is None:
        return ReturnObject(Status.Failure.value, "Invalid Bible Version")
    parameters = (starting_verse_id, ending_verse_id)
    return query_db(db_conn, db_cmd, parameters)


def query_db(db_conn:CMySQLConnection, db_cmd:str, parameters:tuple):
    with db_conn.cursor(buffered=True) as cursor:
        try:
            cursor.execute(db_cmd, parameters)
            if cursor.with_rows==True:
                text = cursor.fetchall()
                return ReturnObject(Status.Success.value, ' '.join([str(verse[0]) for verse in text]))
        except mysql.connector.Error as e:
            #TODO log error 'e'
            return ReturnObject(Status.Failure.value,"Verse not found")


if __name__ == "__main__":
    app.run()