from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

from curl_bible import __version__

router = APIRouter()


@router.get("/versions")
def show_bible_versions():
    """
    Return a list of the bibles supported by this webapp.
    Taken from the 'bible_version_key' table in the DB.

    Args
        None
    Returns:
        (str): A string containing the help message
    Raises:
        None
    """
    return PlainTextResponse(
        content="""
    All current supported versions of the Bible.
    Use the value in 'Version Name' to use that version of the bible, such as:
        curl bible.ricotta.dev/John:3:15-19?version=BBE
        curl bible.ricotta.dev/John:3:15-19?options=version=BBE
    King James Version (KVJ) is the default version

    ╭──────────────┬──────────┬─────────────────────────────┬───────────────╮
    │ Version Name │ Language │ Name of version             │ Copyright     │
    ├──────────────┼──────────┼─────────────────────────────┼───────────────┤
    │     ASV      │ English  │ American Standard Version   │ Public Domain │
    │     BBE      │ English  │ Bible in Basic English      │ Public Domain │
    │     KJV      │ English  │ King James Version          │ Public Domain │
    │     WEB      │ English  │ World English Bible         │ Public Domain │
    │     YLT      │ English  │ Young's Literal Translation │ Public Domain │
    ╰──────────────┴──────────┴─────────────────────────────┴───────────────╯
""",
        status_code=status.HTTP_200_OK,
    )


@router.get("/help")
def display_help():
    """
    Display a help message detailing all supported query methods and options.

    Args:
        None
    Returns:
        book(str): A string containg all supported query methods and options.
    Raises:
        None
    """
    return PlainTextResponse(
        content=f"""
   ______           __   ____  _ __    __
  / ____/_  _______/ /  / __ )(_) /_  / /__
 / /   / / / / ___/ /  / __  / / __ \\/ / _ \\
/ /___/ /_/ / /  / /  / /_/ / / /_/ / /  __/
\\____/\\__,_/_/  /_/  /_____/_/_.___/_/\\___/

Curl Bible - Easily access the bible through curl (HTTPie is also supported)

Supports the following query types (GET):
    • curl bible.ricotta.dev/John:3:15-19
    • curl bible.ricotta.dev/John/3/15-19
    • curl "bible.ricotta.dev?book=John&chapter=3&verse=15-19"
    • curl bible.ricotta.dev/John:3:15:John:4:15

The following options are supported:
    • 'l' or 'length' - the number of lines present in the book
        default value: 20

    • 'w' or 'width' - how many characters will be displayed in each line of the book.
        default value: 80

    • 'c' or 'color_text' - display the returned book with terminal colors
        default value: True

    • 't' or 'text_only' - only returned the unformatted text.
        deafult value: False

    • 'n' or 'verse_number' - Display the associated verse numbers in superscript.
        Default value: False

    • 'v' or 'version' - choose which version of the bible to use.
        Default value: ASV (American Standard Version)
        Tip: curl bible.ricotta.dev/versions to see all supported bible versions.

    These options can be combined on a single parameter for convenience:
        curl bible.ricotta.dev/John:3:15?options=l=50,w=85,c=False,v=BBE
    But may also be separated in key value pairs as parameters:
        curl "bible.ricotta.dev/John:3:15?length=40&color_text=False"
Check out the interactive help menu here: https://bible.ricotta.dev/docs
Version {__version__}
Full information can be found on the README here: https://github.com/connorricotta/curl_bible
""",
        status_code=status.HTTP_200_OK,
    )
