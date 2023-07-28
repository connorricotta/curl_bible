from pydantic import BaseSettings


class Settings(BaseSettings):
    # Matches '3','999','1-999','999-1'
    VERSE_REGEX: str = "^(([0-9]{1,3})|([0-9]{1,3}-[0-9]{1,3}))$"
    # Matches 'John:3:5','Psalms:119:175'
    SINGLE_SEMICOLON_REGEX: str = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
    # Matches 'John:3:5:John:4:3', 'Numbers:7:1:Psalms:119:175'
    MULTI_SEMICOLON_REGEX: str = (
        "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}:[A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
    )
    # Matches 'John:3:1-2','Psalms:119:170-176'
    SINGLE_SEMICOLON_DASH_REGEX: str = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}-[0-9]{1,3})$"
    # Matches 'John 3'
    ENTIRE_CHAPTER_REGEX: str = "^([A-z]*:[0-9]{1,3})$"
    # Matches 'AAA', 'ZZZ'
    VERSION_REGEX: str = "^([A-Z]{3})$"
    REGULAR_TO_SUPERSCRIPT: dict = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
    }


def create_request_verse(**kwargs) -> str:
    if set(kwargs.keys()) == {
        "book",
        "chapter_start",
        "chapter_end",
        "verse_start",
        "verse_end",
    }:
        return f"{kwargs.get('book')} {kwargs.get('chapter_start')}:{kwargs.get('verse_start')} - {kwargs.get('chapter_end')}:{kwargs.get('verse_end')}"
    elif set(kwargs.keys()) == {"book", "chapter", "verse_start", "verse_end"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}:{kwargs.get('verse_start')} - {kwargs.get('verse_end')}"
    elif set(kwargs.keys()) == {"book", "chapter"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}"
    elif set(kwargs.keys()) == {"book", "chapter", "verse"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}:{kwargs.get('verse')}"
