from copy import deepcopy
from functools import lru_cache
from logging import INFO, basicConfig
from math import ceil
from textwrap import TextWrapper

from fastapi import HTTPException, Request, status
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

import curl_bible.db_models as schemas

__version__ = "0.2.7"


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
    RATE_LIMIT: str = "60/minute"
    COLOR_TEXT_DEFAULT: bool = True
    TEXT_ONLY_DEFAULT: bool = False
    VERSION_DEFAULT: str = "ASV"
    LENGTH_DEFAULT: int = 60
    WIDTH_DEFAULT: int = 80
    MAX_SIZE: int = 300
    MIN_SIZE: int = 5
    JSON_DEFAULT: bool = False
    OPTIONS_DEFAULT: str = ""
    VERSE_NUMBERS: bool = True


class Book:
    """
     Standard configuration for the book. Using text escaped characters
     Quick Explainer (for future me)
     Arguments 38 and 48 (custom text-color and background)
     support either:
         • Three args (255 color)
             - 38;5;5
             - 48;5;5
         • Five args (RGB color)
             - 38;2;45;25;67
             - 48;2;45;25;67

    Escape    Ending
     Code    Character  Arg 2
      |          |        |
      V          V        V
     \33[48;5;255m \33[30;1mTest\33[0m
         Λ  Λ  Λ       Λ
         |  |  |       |
        Args 1a-1c   Arg 1
    """

    def __init__(self) -> None:
        brown = "\33[38;2;160;82;45m\33[1m"
        gold = "\33[38;5;229m"
        white = "\33[38;5;231m"
        # white_back = "\33[47m"
        end = "\33[0m"
        self.book_no_color = {
            "top_level": "_",
            "top_start": ".-/|",
            "top_middle": " V ",
            "top_end": "|\\-.\n",
            "middle_start": "||||",
            "middle": "|",
            "middle_end": "||||",
            "bottom_single_pg_start": "||||",
            "bottom_single_pg_middle": " | ",
            "bottom_single_pg_end": "||||",
            "bottom_multi_pg_left": "||/=",
            "bottom_multi_pg_middle": "\\|/",
            "bottom_multi_pg_end": "=\\||",
            "bottom_final_pg_left": "`---",
            "bottom_final_pg_middle": "~___~",
            "bottom_final_pg_end": "---𝅪",
        }

        self.book_color = {
            "top_level": "\33[37;1m_\33[0m",
            "top_start": f"{brown}.{end}{gold}-/{end}|",
            "top_middle": " V ",
            "top_end": f"|{end}{gold}\\-{end}{brown}.{end}\n",
            "middle_start": f"{brown}|{end}{gold}||{end}|",
            "middle": "|",
            "middle_end": f"{white}|{end}{gold}||{end}{brown}|{end}",
            "bottom_single_pg_start": f"{brown}|{end}{gold}||{end}{white}|{end}",
            "bottom_single_pg_middle": " | ",
            "bottom_single_pg_end": f"|{end}{gold}||{end}{brown}|{end}",
            "bottom_multi_pg_left": f"{brown}|{end}{gold}|/=",
            "bottom_multi_pg_middle": f"\33[0m\\|/{gold}",
            "bottom_multi_pg_end": f"=\\|{end}{brown}|{end}",
            "bottom_final_pg_left": f"{brown}`---",
            "bottom_final_pg_middle": "~___~",
            "bottom_final_pg_end": f"---𝅪{end}",
        }

    def get_no_color(self) -> dict():
        return self.book_no_color

    def get_color(self) -> dict():
        return self.book_color


@lru_cache()
def create_settings():
    return Settings()


def create_request_verse(db, **kwargs) -> str:
    book_list = schemas.KeyAbbreviationsEnglish
    book_id = (
        db.query(book_list).filter(book_list.name == kwargs.get("book")).first().book
    )
    full_book_name = (
        db.query(book_list)
        .filter(book_list.book == book_id)
        .filter(book_list.primary == "1")
        .all()[-1]
        .name
    )
    kwargs["book"] = full_book_name
    if set(kwargs.keys()) == {
        "book",
        "chapter_start",
        "chapter_end",
        "verse_start",
        "verse_end",
    }:
        return f"{kwargs.get('book')} {kwargs.get('chapter_start')}:{kwargs.get('verse_start')} - {kwargs.get('chapter_end')}:{kwargs.get('verse_end')}"
    if set(kwargs.keys()) == {"book", "chapter", "verse_start", "verse_end"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}:{kwargs.get('verse_start')}-{kwargs.get('verse_end')}"
    if set(kwargs.keys()) == {"book", "chapter"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}"
    if set(kwargs.keys()) == {"book", "chapter", "verse"}:
        return f"{kwargs.get('book')} {kwargs.get('chapter')}:{kwargs.get('verse')}"


def is_bool(bool_test: str) -> bool:
    if isinstance(bool_test, bool):
        return bool_test
    return bool_test.lower() in ("yes", "true", "t", "1")


settings = create_settings()


class OptionsNames:
    short_to_long = {
        "color": "color_text",
        "text": "text_only",
        "numbers": "verse_numbers",
        "json": "return_json",
        "c": "color_text",
        "l": "length",
        "t": "text_only",
        "w": "width",
        "v": "version",
        "n": "verse_numbers",
        "j": "return_json",
    }

    values = {
        "color_text": settings.COLOR_TEXT_DEFAULT,
        "length": settings.LENGTH_DEFAULT,
        "text_only": settings.TEXT_ONLY_DEFAULT,
        "width": settings.WIDTH_DEFAULT,
        "version": settings.VERSION_DEFAULT,
        "verse_numbers": settings.VERSE_NUMBERS,
        "return_json": settings.JSON_DEFAULT,
    }

    def to_long(self, option):
        """
        Return the full name of the option
        """
        if option in self.short_to_long:
            return self.short_to_long[option]
        else:
            return option


class Options(BaseModel):
    color_text: bool | None = Field(default=True, alias="c")
    text_only: bool | None = Field(default=settings.TEXT_ONLY_DEFAULT, alias="t")
    version: str | None = Field(default=settings.VERSION_DEFAULT, alias="v")
    length: int | None = Field(
        default=settings.LENGTH_DEFAULT,
        gt=settings.MIN_SIZE,
        lt=settings.MAX_SIZE,
        alias="l",
    )
    width: int | None = Field(
        default=settings.WIDTH_DEFAULT,
        gt=settings.MIN_SIZE,
        lt=settings.MAX_SIZE,
        alias="w",
    )
    verse_numbers: bool | None = Field(
        default=settings.VERSE_NUMBERS,
        validation_alias=AliasChoices("n", "verse_numbers", "numbers"),
    )
    return_json: bool | None = Field(
        default=False,
        validation_alias=AliasChoices("j", "return_json", "json"),
    )
    options: str | None = None
    request: Request = None

    model_config = ConfigDict(arbitrary_types_allowed=True, validate_return=True)

    # pylint: disable=no-self-argument
    @field_validator("request")
    def request_validator(cls, user_options, values):
        if user_options is None or len(user_options.query_params) == 0:
            return values
        default_options = OptionsNames()
        params = dict(user_options.query_params)
        for param in params:
            request_value = params[param]
            full_name = default_options.to_long(param)
            if full_name in values.data:
                if full_name in [
                    "color_text",
                    "text_only",
                    "verse_numbers",
                    "return_json",
                ]:
                    values.data[full_name] = is_bool(request_value)
                if (
                    full_name in ["length", "width"]
                    and (isinstance(request_value, int) or params[param].isnumeric())
                    and (settings.MIN_SIZE < int(request_value) <= settings.MAX_SIZE)
                ):
                    values.data[full_name] = int(request_value)

                if full_name == "version" and len(request_value) == 3:
                    values.data[full_name] = request_value.upper()

        return values

    # pylint: disable=no-self-argument
    @field_validator("options")
    def name_must_contain_space(cls, user_options, values):
        """
        Parse the options parameter the user passes in a list of options all attached to the option parameter.
        Takes the argument "options=w=78,v=BBE,length=85,c=no", and update the options Object
        """
        default_options = OptionsNames()
        default_values = deepcopy(default_options.values)
        if user_options == "" or user_options is None:
            return user_options

        # Parse the options string into its constitutent parts
        # Turns string 'w=78,v=BBE,length=85,c=no' into list ['w=78', 'v=BBE', 'length=85', 'c=no']
        parsed_option_string = (
            user_options.replace("o=", "")
            .replace("options=", "")
            .replace("'", "")
            .split(",")
        )

        option_list = [i.split("=") for i in parsed_option_string]

        # Parse through the options and update the dictionary if the option is there
        for option in option_list:
            option_name = option[0]
            option_value = option[1]

            # If the user passes in a valid option, update the default value
            #   Ex: 'l':45 will be converted into 'length':45 and replace the default value
            default_values[default_options.to_long(option_name)] = option_value

        # Update the options passed to FastAPI to match the default_options dict.
        values.data["color_text"] = is_bool(default_values.get("color_text"))
        values.data["text_only"] = is_bool(default_values.get("text_only"))
        values.data["verse_numbers"] = is_bool(default_values.get("verse_numbers"))
        values.data["return_json"] = is_bool(default_values.get("return_json"))

        # Ensure that 'width' or 'length' are integers and they are greater than 0
        if (isinstance(default_values.get("length"), int)) or (
            str(default_values.get("length")).isnumeric()
            and int(default_values.get("length")) > 0
        ):
            values.data["length"] = int(default_values["length"])

        if (isinstance(default_values["width"], int)) or (
            str(default_values["width"]).isnumeric()
            and int(default_values["width"]) > 0
        ):
            values.data["width"] = int(default_values["width"])

        if len(default_values["version"]) == 3:
            values.data["version"] = default_values["version"].upper()

        return user_options

    def update(self, user_options: dict) -> str:
        """
        Parse 'small' arguments passed in separately like 'w=15&l=54' and update the
        user Options object
        """
        params = dict(user_options.query_params)
        options_set = set(("l", "w", "v", "t", "c", "n", "j"))
        # Only parse them if the user passes in options with one of the values in 'options_set'
        short_options = options_set.intersection(params)
        if short_options is not None:
            for key in short_options:
                value = params[key]
                if key == "l":
                    if str.isnumeric(value) and int(value) > 0:
                        self.length = int(value)
                elif key == "w":
                    if str.isnumeric(value) and int(value) > 0:
                        self.width = int(value)
                elif key == "c":
                    self.color_text = is_bool(value)
                elif key == "t":
                    self.text_only = is_bool(value)
                elif key == "v":
                    if len(value) == 3:
                        self.version = value.upper()
                elif key == "n":
                    self.verse_numbers = is_bool(value)
                elif key == "j":
                    self.return_json = is_bool(value)
        return " "


class UserError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ProgrammerError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


def create_book(bible_verse: str, user_options: Options, request_verse: dict):
    """
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
    """
    book = Book()
    basicConfig(level=INFO, filename="config.log")

    if user_options is not None:
        length = user_options.length
        width = user_options.width
        if user_options.color_text:
            book_parts = book.get_color()
        else:
            book_parts = book.get_no_color()
        splitter = TextWrapper(width=user_options.width // 2 - 2)

    else:
        width = 80
        length = 20
        splitter = TextWrapper(width=38)
        book_parts = book.get_color()

    formatted_text = splitter.wrap(bible_verse)
    final_book_middle_array = []
    page_width = width // 2
    # Add three lines to the start of the verses
    formatted_verse = "".join(request_verse)
    spaced_verse = (page_width - len(formatted_verse)) // 2
    formatted_text.insert(0, "")
    formatted_text.insert(
        0, " " * spaced_verse + formatted_verse + " " * (spaced_verse - 1)
    )
    formatted_text.insert(0, "")

    # Generating the book in this way allows for the easy modification of
    # book generation.
    final_book_top = (
        "    "
        + book_parts["top_level"] * page_width
        + " "
        + book_parts["top_level"] * page_width
        + "    \n"
        + book_parts["top_start"]
        + " " * (page_width - 1)
        + book_parts["top_middle"]
        + " " * (page_width - 1)
        + book_parts["top_end"]
    )

    for i in range((length // 2)):
        try:
            if i < len(formatted_text):
                text = formatted_text[i]
                second_text_index = ceil(length / 2) + i

            if i == (length // 2 - 1):
                if len(formatted_text) == second_text_index and (
                    len(formatted_text[second_text_index]) >= page_width - 3
                ):
                    formatted_text[second_text_index] = (
                        formatted_text[second_text_index][:-3] + "..."
                    )
                else:
                    if len(formatted_text[second_text_index] + "...") > page_width - 2:
                        # Strip out extra ... if they exist
                        formatted_text[second_text_index] += "..."
                        formatted_text[second_text_index] = formatted_text[
                            second_text_index
                        ][: page_width - 2]
                    else:
                        formatted_text[second_text_index] += "..."
            # If too big for second text, only display the first
            if i < len(formatted_text) and second_text_index >= len(formatted_text):
                final_book_middle_array.append(
                    book_parts["middle_start"]
                    + f" {text}"
                    + " " * (page_width - (len(text) + 1))
                    + book_parts["middle"]
                    + " " * (page_width)
                    + book_parts["middle_end"]
                    + "\n"
                )  # nopep8
            # If too big for first, don't display any text
            elif i >= len(formatted_text):
                final_book_middle_array.append(
                    book_parts["middle_start"]
                    + " " * (page_width)
                    + book_parts["middle"]
                    + " " * (page_width)
                    + book_parts["middle_end"]
                    + "\n"
                )  # nopep8
            # Display text regularly
            else:
                final_book_middle_array.append(
                    book_parts["middle_start"]
                    + f" {text}"
                    + " " * (page_width - (len(text) + 1))
                    + book_parts["middle"]
                    + f" {formatted_text[second_text_index]}"
                    + " " * (page_width - (len(formatted_text[second_text_index]) + 1))
                    + book_parts["middle_end"]
                    + "\n"
                )  # nopep8

        except Exception as e:
            print(e)

            continue

    final_bottom_single_pg = (
        book_parts["bottom_single_pg_start"]
        + book_parts["top_level"] * (page_width - 1)
        + book_parts["bottom_single_pg_middle"]
        + book_parts["top_level"] * (page_width - 1)
        + book_parts["bottom_single_pg_end"]
        + "\n"
    )

    final_bottom_multi_pg = (
        book_parts["bottom_multi_pg_left"]
        + "=" * (page_width - 1)
        + book_parts["bottom_multi_pg_middle"]
        + "=" * (page_width - 1)
        + book_parts["bottom_multi_pg_end"]
        + "\n"
    )

    final_bottom_final_pg = (
        book_parts["bottom_final_pg_left"]
        + "-" * (page_width - 2)
        + book_parts["bottom_final_pg_middle"]
        + "-" * (page_width - 2)
        + book_parts["bottom_final_pg_end"]
        + "\n"
    )

    return (
        final_book_top
        + "".join(final_book_middle_array)
        + final_bottom_single_pg
        + final_bottom_multi_pg
        + final_bottom_final_pg
    )


def multi_query(db, **kwargs) -> str:
    options = kwargs.pop("options")
    request = kwargs.pop("request")
    referer = request.headers.get("referer")
    if request is not None and referer is not None and "/docs" in referer:
        options.text_only = True
    if options is not None:
        if options.version == "ASV":
            version = schemas.TableASV
        elif options.version == "BBE":
            version = schemas.TableBBE
        elif options.version == "JKV":
            version = schemas.TableKJV
        elif options.version == "WEB":
            version = schemas.TableWEB
        elif options.version == "YLT":
            version = schemas.TableYLT
    else:
        version = schemas.TableASV

    # Query single verse
    if {"book", "chapter", "verse"} == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
                .filter(version.verse == kwargs.get("verse"))
            ).all()

        except Exception as e:
            raise ProgrammerError(repr(e)) from e

    # Entire chapter
    elif {"book", "chapter"} == set(kwargs.keys()):
        try:
            data = (
                db.query(version)
                .filter(version.book == kwargs.get("book"))
                .filter(version.chapter == kwargs.get("chapter"))
            ).all()

        except Exception as e:
            raise ProgrammerError(repr(e)) from e

    # Multi verse, same chapter
    elif {"book", "chapter", "verse_start", "verse_end"} == set(kwargs.keys()):
        try:
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

        except Exception as e:
            raise ProgrammerError(repr(e)) from e

    # Multi verse, different chapter
    elif set(
        ["book", "chapter_start", "chapter_end", "verse_start", "verse_end"]
    ) == set(kwargs.keys()):
        try:
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

        except Exception as e:
            raise ProgrammerError(repr(e)) from e
    else:
        raise UserError("verse not found")
    if data is not None:
        if options.verse_numbers:
            # Converts verse numbers into their uppercase version
            text = " ".join(
                [
                    "".join(
                        [
                            settings.REGULAR_TO_SUPERSCRIPT.get(num)
                            for num in [*str(query.verse)]
                        ]
                    )
                    + query.text
                    for query in data
                ]
            )
            kwargs["text"] = text
            kwargs["options"] = options
            return kwargs

        text = " ".join([query.text for query in data])
        kwargs["text"] = text
        kwargs["options"] = options
        return kwargs


def flatten_args(db, **kwargs):
    """
    Convert regular bible verses into IDs
    """
    # if "request" in
    for argument in [
        "chapter",
        "chapter_start",
        "chapter_end",
        "verse",
        "verse_start",
        "verse_end",
    ]:
        if argument in kwargs:
            if isinstance(kwargs.get(argument), int):
                kwargs[argument] = str(kwargs.get(argument))
            if not str.isnumeric(kwargs.get(argument)):
                raise UserError(f"Invalid {argument}! {argument} is not a number!")

            kwargs[argument] = "0" * (3 - len(kwargs.get(argument))) + kwargs.get(
                argument
            )

    if "book" in kwargs:
        data = (
            db.query(schemas.KeyAbbreviationsEnglish)
            .filter(schemas.KeyAbbreviationsEnglish.name == kwargs.get("book"))
            .filter(schemas.KeyAbbreviationsEnglish.primary == "1")
        ).first()
        if data is None:
            data = (
                db.query(schemas.KeyAbbreviationsEnglish).filter(
                    schemas.KeyAbbreviationsEnglish.name == kwargs.get("book")
                )
            ).first()
        if data is not None:
            kwargs["book"] = str(data.book)
        else:
            raise UserError(f"Book {kwargs.get('book')} not found.")

    return kwargs
