# Bible Webapp
# Query the Holy Bible using curl
# Author: CR

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


@app.route("/",methods=["POST","GET"])
def bible():
    # Check for arguments version
    if "book" in request.args and "chapter" in request.args and "verse" in request.args:
        book = request.args['book']
        chapter = request.args['chapter']
        verse = request.args['verse']

        db_conn = connect_to_db()
        if db_conn is None:
            return ("Cannot connect to local Database", 500)

        # Set a default version if none is specified
        if "version" in request.args:
            version = request.args['version']
        else:
            version = "t_asv"

        # Correlate book name to book id        
        book_id = book_to_id(book, db_conn)
        if book_id[0]==Status.Failure.value:
            return (f"Invalid book selection: {book}\n", 400)
        else:
            book_id = str(book_id[1])

        # Check for multiple quotes
        if '-' in verse:
            [start,stop] = verse.split("-")
            # Make sure that the verses are valid
            if not str.isnumeric(start) or not str.isnumeric(stop):
                return (f"Invalid Verse {verse}\n", 400)
            result = query_multiple_quotes(
                starting_book=book_id,
                starting_chapter=chapter,
                starting_verse=start,
                ending_book=book_id,
                ending_chapter=chapter,
                ending_verse=stop,
                database_connection=db_conn,
                text_only=True,
                book_version=version
            )

            if result[0] == Status.Success.value:
                return (result[1]+"\n", 200)
            else:
                return (result[1]+"\n", 400)

        if book_id is not None and isinstance(book_id, int):
            result = query_single_quote(
                str(book_id), 
                chapter,
                verse,
                db_conn,
                text_only=True,
                book_version=version
            )
            if result[0] == Status.Success.value:
                return result[1]+"\n"
            else:
                return (result[1]+"\n", 400)
    
    return ("Error", 400)
   

@app.route('/<book>/<chapter>/<verse>')
def bible_thing(book, chapter, verse):
    db_conn = connect_to_db()
    book_id = book_to_id(book, db_conn)
    if book_id is not None and isinstance(book_id, int):
        return query_single_quote(str(book_id), chapter, verse, db_conn, True) + "\n"


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


def set_book_version(book_version:str, single_or_multiple:bool) -> str:
# Cannot passed in book_version, must be done manually to prevent SQL injection
    if single_or_multiple == Query.Single.value:
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
    else:
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
    return run_db_command(
        db_conn=database_connection,
        cmd=db_cmd,
        parameters=db_parameters,
        single_or_multiple=Query.Single.value
    )


def run_db_command(db_conn:CMySQLConnection, cmd:str, parameters:tuple, single_or_multiple:int) -> tuple:
     with db_conn.cursor() as cursor:
        try:
            cursor.execute(cmd, parameters)
            if cursor.with_rows==True:
                if single_or_multiple == Query.Single.value:
                    result = cursor.fetchone()
                elif single_or_multiple == Query.Multiple.value:
                    result = cursor.fetchall()
                    return (Status.Success.value, ' '.join([x[0] for x in result]))
                if result != None:
                    return (Status.Success.value, result[0])
                else:
                    return (Status.Failure.value, "No data was returned")
        except mysql.connector.Error as e:
            #TODO log error 'e'
            return (Status.Failure.value, "Database Error")


def query_single_quote(book:str, chapter:str, verse:str, database_connection, text_only:bool, book_version:str) -> tuple:
    verse_id = "0"*(2-len(book))+book + "0"*(3-len(chapter))+chapter + "0"*(3-len(verse))+verse
    db_cmd = set_book_version(book_version, Query.Single.value)
    if db_cmd is None:
        return (1,f"Invalid book version {book_version}")
    
    return run_db_command(
        db_conn=database_connection, 
        cmd=db_cmd,
        parameters=(verse_id,),
        single_or_multiple=Query.Single.value
    )


def query_multiple_quotes(starting_book:str, starting_chapter:str, starting_verse:str, 
                          ending_book:str, ending_chapter:str, ending_verse:str, 
                          database_connection:CMySQLConnection, text_only:bool, book_version:str) -> str:

    starting_verse_id = "0"*(2-len(starting_book))+starting_book + \
                        "0"*(3-len(starting_chapter))+starting_chapter + \
                        "0"*(3-len(starting_verse))+starting_verse

    ending_verse_id =   "0"*(2-len(ending_book))+ending_book + \
                        "0"*(3-len(ending_chapter))+ending_chapter + \
                        "0"*(3-len(ending_verse))+ending_verse

    db_cmd = set_book_version(book_version, 1)
    db_parameters = (starting_verse_id, ending_verse_id)
    return run_db_command(
        db_conn=database_connection,
        cmd=db_cmd,
        parameters=db_parameters,
        single_or_multiple=Query.Multiple.value
    )


if __name__ == "__main__":
    app.run()