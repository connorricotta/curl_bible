try:
    from fastapi_bible import app
except Exception as e:
    from python.fastapi_bible import app

if __name__ == "__main__":
    app.run()
