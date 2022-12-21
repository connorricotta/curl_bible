from enum import Enum
from math import ceil
from textwrap import TextWrapper
from logging import basicConfig, INFO, warning
from pydantic import BaseModel, Field, validator

from book_config import Book

COLOR_TEXT_DEFAULT = True
TEXT_ONLY_DEFAULT = False
VERSION_DEFAULT = "ASV"
LENGTH_DEFAULT = 60
WIDTH_DEFAULT = 80
OPTIONS_DEFAULT = ""
VERSE_NUMBERS = False

# Matches '3','999','1-999','999-1'
VERSE_REGEX = "^(([0-9]{1,3})|([0-9]{1,3}-[0-9]{1,3}))$"
# Matches 'John:3:5','Psalms:119:175'
SINGLE_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:5:John:4:3', 'Numbers:7:1:Psalms:119:175'
MULTI_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}:[A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:1-2','Psalms:119:170-176'
SINGLE_SEMICOLON_DASH_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}-[0-9]{1,3})$"
# Matches 'John 3'
ENTIRE_CHAPTER_REGEX = "^([A-z]*:[0-9]{1,3})$"
# Matches 'AAA', 'ZZZ'
VERSION_REGEX = "^([A-Z]{3})$"


# Because these superscripts are in different Unicode blocks, just manually replace values.
REGULAR_TO_SUPERSCRIPT = {
    '0': "⁰",
    '1': "¹",
    '2': "²",
    '3': "³",
    '4': "⁴",
    '5': "⁵",
    '6': "⁶",
    '7': "⁷",
    '8': "⁸",
    '9': "⁹"

}

class OptionsNames:
    """
    Contains
    """

    short_to_long = {
        "c": "color_text",
        "l": "length",
        "t": "text_only",
        "w": "width",
        "v": "version",
        "n": "verse_numbers",
    }

    values = {
        "color_text": COLOR_TEXT_DEFAULT,
        "length": LENGTH_DEFAULT,
        "text_only": TEXT_ONLY_DEFAULT,
        "width": WIDTH_DEFAULT,
        "version": VERSION_DEFAULT,
        "verse_numbers": VERSE_NUMBERS,
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
    color_text: bool | None = Field(default=True)
    text_only: bool | None = Field(default=TEXT_ONLY_DEFAULT)
    version: str | None = Field(default=VERSION_DEFAULT)
    length: int | None = Field(default=LENGTH_DEFAULT, gt=0)
    width: int | None = Field(default=WIDTH_DEFAULT, gt=0)
    verse_numbers: bool | None = Field(default=VERSE_NUMBERS)
    options: str | None

    @validator("options")
    def contains_options(cls, user_options, values):
        """
        In case the user passes in a list of options all attached to the option parameter, parse them here.
        Takes the argument "options=w=78,v=BBE,length=85,c=no", and update the options Object
        """

        default_options = OptionsNames()
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
            default_options.values[default_options.to_long(option_name)] = option_value

        # Update the options passed to FastAPI to match the default_options dict.
        values["color_text"] = is_bool(default_options.values["color_text"])
        values["text_only"] = is_bool(default_options.values["text_only"])
        values["verse_numbers"] = is_bool(default_options.values["verse_numbers"])

        # Ensure that 'width' or 'length' are integers and they are greater than 0
        if (type(default_options.values["length"]) == int) or (
            str.isnumeric(default_options.values["length"])
            and int(default_options.values["length"]) > 0
        ):
            values["length"] = int(default_options.values["length"])
        if (type(default_options.values["width"]) == int) or (
            str.isnumeric(default_options.values["width"])
            and int(default_options.values["width"]) > 0
        ):
            values["width"] = int(default_options.values["width"])
        if len(default_options.values["version"]) == 3:
            values["version"] = default_options.values["version"].upper()

        return user_options

    def update(self, user_options: dict) -> str:
        """
        Parse 'small' arguments passed in separately like 'w=15&l=54' and update the
        user Options object
        """
        params = dict(user_options.query_params)
        options_set = set(("l", "w", "v", "t", "c", "n"))
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
        return ""


class Status(Enum):
    Success = 0
    Failure = 401
    MajorFailure = 501


class ReturnObject:
    def __init__(self, status: int, content: str) -> None:
        self.status = status
        self.content = content

    def get_content(self):
        return self.content

    def get_status(self):
        return self.status

    def get_error(self):
        return self.content

    def is_error(self):
        return self.status.value != Status.Success.value


def is_bool(bool_test):
    if type(bool_test) == bool:
        return bool_test
    return bool_test.lower() in ("yes", "true", "t", "1")


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
        splitter = TextWrapper(width=(user_options.width // 2 - 2))

    else:
        width = 80
        length = 20
        splitter = TextWrapper(width=38)
        book_parts = book.get_color()

    formatted_text = splitter.wrap(bible_verse)
    final_book_middle_array = []
    page_width = width // 2
    # Add three lines to the start of the verses
    # if len(request_verse) == 3:
    #     formatted_verse = f"{request_verse[0]} {request_verse[1]}:{request_verse[2]}"
    # elif len(request_verse) == 6:
    #     formatted_verse = f"{request_verse[0]} {request_verse[1]}:{request_verse[2]}-{request_verse[3]} {request_verse[4]}:{request_verse[5]} "
    # else:
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
                if len(formatted_text[second_text_index]) >= page_width - 3:
                    formatted_text[second_text_index] = (
                        formatted_text[second_text_index][:-3] + "..."
                    )
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
            warning("Thing no work " + str(e))
            # TODO add exeception logging and fix bug here
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

    return ReturnObject(
        Status.Success,
        final_book_top
        + "".join(final_book_middle_array)
        + final_bottom_single_pg
        + final_bottom_multi_pg
        + final_bottom_final_pg,
    )
