from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from curl_bible import schema
from curl_bible.config import Options
from curl_bible.database import engine, get_database_session

app = FastAPI()

schema.Base.metadata.create_all(bind=engine)


class UserError(HTTPException):
    def __init__(self, detail: str):
        self.detail = detail
        self.status_code = status.HTTP_400_BAD_REQUEST


@app.get("/asv/{book}/{chapter_start}/{verse_start}/{chapter_end}/{verse_end}")
async def mutli_verse_different_chapter(
    book: str,
    chapter_start: str,
    verse_start: str,
    chapter_end: str,
    verse_end: str,
    db: Session = Depends(get_database_session),
):
    return multi_query(
        db=db,
        book=book,
        chapter_start=chapter_start,
        chapter_end=chapter_end,
        verse_start=verse_start,
        verse_end=verse_end,
    )


@app.get("/asv/{book}/{chapter}/{verse}")
async def single_verse(
    book: str,
    chapter: str,
    verse: str,
    db: Session = Depends(get_database_session),
    options: Options = Depends(),
):
    return multi_query(db=db, book=book, chapter=chapter, verse=verse, options=options)


@app.get("/asv/{book}/{chapter}/{verse_start}/{verse_end}")
async def mutli_verse_same_chapter(
    book: str,
    chapter: str,
    verse_start: str,
    verse_end: str,
    db: Session = Depends(get_database_session),
):
    return multi_query(
        db=db, book=book, chapter=chapter, verse_start=verse_start, verse_end=verse_end
    )


@app.get("/asv/{book}/{chapter}")
async def entire_chapter(
    book: str,
    chapter: str,
    db: Session = Depends(get_database_session),
):
    return multi_query(db=db, book=book, chapter=chapter)


def multi_query(db, **kwargs) -> str:
    options = kwargs.pop("options")
    if options is not None:
        if options.version == "ASV":
            version = schema.TableASV
        elif options.version == "BBE":
            version = schema.TableBBE
        elif options.version == "JKV":
            version = schema.TableKJV
        elif options.version == "WEB":
            version = schema.TableWEB
        elif options.version == "YLT":
            version = schema.TableYLT
    else:
        version = schema.TableASV

    if set(["book", "chapter", "verse"]) == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
                .filter(version.verse == kwargs.get("verse"))
            ).all()

        except Exception as e:
            raise HTTPException(detail=repr(e))
            print(e)

    # Entire chapter
    elif set(["book", "chapter"]) == set(kwargs.keys()):
        data = (
            db.query(version)
            .filter(version.book == kwargs.get("book"))
            .filter(version.chapter == kwargs.get("chapter"))
        ).all()

    # Multi verse, same chapter
    elif set(["book", "chapter", "verse_start", "verse_end"]) == set(kwargs.keys()):
        data = (
            db.query(version)
            .filter(version.book == kwargs.get("book"))
            .filter(version.chapter == kwargs.get("chapter"))
            .filter(
                version.verse.between(
                    kwargs.get("verse_start"), kwargs.get("verse_end")
                )
            )
        ).all()

    # Multi verse, different chapter
    elif set(
        ["book", "chapter_start", "chapter_end", "verse_start", "verse_end"]
    ) == set(kwargs.keys()):
        data = (
            db.query(version)
            .filter(version.book == kwargs.get("book"))
            .filter(
                version.chapter.between(
                    kwargs.get("chapter_start"), kwargs.get("chapter_end")
                )
            )
            .filter(
                version.id.between(
                    "".join(
                        [
                            kwargs.get("book"),
                            kwargs.get("chapter_start"),
                            kwargs.get("verse_start"),
                        ]
                    ),
                    "".join(
                        [
                            kwargs.get("book"),
                            kwargs.get("chapter_end"),
                            kwargs.get("verse_end"),
                        ]
                    ),
                )
            )
        ).all()

    else:
        raise UserError("verse not found")
    if data is not None:
        return " ".join([query.text for query in data])
    # else:
    #     return models.DBReturn(
    #         meta=models.Meta(status="error", message="Verse not found"), content=""
    #     )
    # if data is not None:
    #     return str(data.verse) + data.text
    # else:
    #     return models.DBReturn(
    #         meta=models.Meta(status="error", message="Verse not found"), content=""
    #     )
