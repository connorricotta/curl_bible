from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from curl_bible import models, schema
from curl_bible.database import engine, get_database_session

app = FastAPI()

schema.Base.metadata.create_all(bind=engine)


@app.get("/asv/{book}/{chapter}/{verse}")
async def get_hero(
    book: str, chapter: str, verse: str, db: Session = Depends(get_database_session)
):
    data = (
        db.query(schema.TableASVNew)
        .filter(schema.TableASVNew.book == book)
        .filter(schema.TableASVNew.chapter == chapter)
        .filter(schema.TableASVNew.verse == verse)
    ).first()

    if data is not None:
        return data
    else:
        return models.DBReturn(
            meta=models.Meta(status="error", message="Verse not found"), content=""
        )
