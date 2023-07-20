from typing import Union

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from curl_bible import models, schema
from curl_bible.database import engine, get_database_session

app = FastAPI()

schema.Base.metadata.create_all(bind=engine)


@app.get("/asv/{book}/{chapter}/{verse}/{version}")
async def get_hero(
    book: str,
    chapter: str,
    verse: str,
    version: Union[str, None] = None,
    db: Session = Depends(get_database_session),
):
    return multi_query(db=db, book=book, chapter=chapter, verse=verse, version=version)


def multi_query(db, **kwargs) -> str:
    if "version" in kwargs.keys():
        if kwargs.get("version").lower() in ["t_asv", "asv"]:
            version = schema.TableASV
        elif kwargs.get("version").lower() in ["t_bbe", "bbe"]:
            version = schema.TableBBE
        elif kwargs.get("version").lower() in ["t_kjv", "kjv"]:
            version = schema.TableKJV
        elif kwargs.get("version").lower() in ["t_web", "web"]:
            version = schema.TableWEB
        elif kwargs.get("version").lower() in ["t_ylt", "ylt"]:
            version = schema.TableYLT
    else:
        version = schema.TableASV

    if set(["book", "chapter", "verse"]).issubset(set(kwargs.keys())):
        data = (
            db.query(version)
            .filter(version.book == kwargs.get("book"))
            .filter(version.chapter == kwargs.get("chapter"))
            .filter(version.verse == kwargs.get("verse"))
        ).first()
    # 'SELECT t from t_asv where id like %s'
    if set(["book", "chapter"]).issubset(set(kwargs.keys())):
        data = (
            db.query(version)
            .filter(version.book == kwargs.get("book"))
            .filter(version.chapter == kwargs.get("chapter"))
        ).all()
        return "".join([query.text for query in data])

    if data is not None:
        return str(data.verse) + data.text
    else:
        return models.DBReturn(
            meta=models.Meta(status="error", message="Verse not found"), content=""
        )
