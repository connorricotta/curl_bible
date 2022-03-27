from freebible import bibles
from flask import Flask, request

# print(bibles.print("Gen"))

app = Flask(__name__)

@app.route("/",methods=["POST","GET"])
def bible():
    if "book" in request.args and "chapter" in request.args and "verse" in request.args:
        # book = bibles.print(request.args['book'], request.args['chapter'], request.args['verse'])[1]
        # return f"{book.book_key}:{book.ID}-{book.chapID} {book.text}\n"
        return bibles.web.quote(request.args['book'], request.args['chapter'], request.args['verse']).text+"\n"

    if request.method == 'POST':
        print("Data received from Webhook is: ", request.json)
        return "Webhook received!"
    print("test")
    return "Hello World!"

if __name__ == "__main__":
    app.run()