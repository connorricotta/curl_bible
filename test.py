from flask import Flask, request
import mysql.connector
from mysql.connector import Error


app = Flask(__name__)




@app.route("/",methods=["POST","GET"])
def bible():
    if "book" in request.args and "chapter" in request.args and "verse" in request.args:
        # book = bibles.print(request.args['book'], request.args['chapter'], request.args['verse'])[1]
        # return f"{book.book_key}:{book.ID}-{book.chapID} {book.text}\n"
        # return bibles.web.quote(request.args['book'], request.args['chapter'], request.args['verse']).text+"\n"
        db_conn = connect_to_db()

        if db_conn is None:
            return ("Cannot connect to local Database", 500)
        
        book_id = book_to_id(request.args['book'], db_conn)
        if book_id is not None and isinstance(book_id, int):
            result = query_bible(book=str(book_id), chapter=request.args['chapter'], verse=request.args['verse'], db_conn=db_conn)
            return result+"\n"
    
    return ("Error", 400)
   

@app.route('/<book>/<chapter>/<verse>')
def bible_thing(book, chapter, verse):
    db_conn = connect_to_db()
    book_id = book_to_id(book, db_conn)
    if book_id is not None and isinstance(book_id, int):
        return query_bible(str(book_id), chapter, verse, db_conn) + "\n"
#   return f"Result is {book} {chapter} {verse}"


def connect_to_db():
    """ Connect to MySQL database """
    conn = None
    
    try:
        conn = mysql.connector.connect(host='localhost',database='bible',user='root',password='secret',port='33060')
        if conn.is_connected():
            return conn

    except Error as e:
        # TODO add logging
        return None


def book_to_id(book:str, db_conn) -> str:
    with db_conn.cursor() as cursor:
        cmd = "SELECT b from key_abbreviations_english where a=%s"
        parameters = (book,)
        cursor.execute(cmd, parameters)
        if cursor.with_rows:
            return cursor.fetchone()[0]
        return None


def query_bible(book:str, chapter:str, verse:str, db_conn) -> str:
    verse_id = "0"*(2-len(book))+book + "0"*(3-len(chapter))+chapter + "0"*(3-len(verse))+verse
    with db_conn.cursor() as cursor:
        cmd = "SELECT t from t_asv where id=%s"
        parameters = (verse_id,)
        cursor.execute(cmd, parameters)
        if cursor.with_rows:
            return cursor.fetchone()[0]

if __name__ == "__main__":
    app.run()