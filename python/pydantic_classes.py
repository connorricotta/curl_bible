from functools import wraps

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field, ValidationError, validator
from starlette import requests

from options import *

app = FastAPI()


@app.get("/")
async def parse_options(request: requests.Request, options: Options = Depends()):
    options.update(request)
    return dict(request.query_params) | dict(options)


class Regex(BaseModel):
    verse: str = Field(regex="^(([0-9]{1,3})|([0-9]{1,3}-[0-9]{1,3}))$")


if __name__ == "__main__":

    try:
        r = Regex(verse="1-3")
        print(r)
        opt = Options(opt="test")
        print(opt)
    except Exception as e:
        print(e)

    try:
        # Default values. Over-written if new options are passed in from the options object
        options_dict = {
            "color_text": "True",
            "length": "20",
            "text_only": "False",
            "width": "80",
            "version": "ASV",
        }
        # Maps all aliases into it's longest version
        options_map = {
            "c": "color_text",
            "l": "length",
            "t": "text_only",
            "w": "width",
            "v": "version",
            "color_text": "color_text",
            "length": "length",
            "text_only": "text_only",
            "width": "width",
            "version": "version",
        }
        # Convert string of options into a dictionary of values
        option_string = "o=w=78,v=BBE,text_only='yes',c='no'"
        parsed_option_string = (
            option_string.strip("o=").strip("options").replace("'", "").split(",")
        )
        option_list = [i.split("=") for i in parsed_option_string]

        """
        Ensure that the dictionary has full entries and values.
        Minimized values are converted into their full values.
        Ex:
            ['w','78']      => {'width': '78'}
            ['version,'58'] => {'version': '58'}
        """
        for option in option_list:
            options_dict[options_map[option[0]]] = option[1]

        # n = Options(
        #     color_text=options_dict["color_text"],
        #     length=options_dict["length"],
        #     text_only=options_dict["text_only"],
        #     width=options_dict["width"],
        #     version=options_dict["version"],
        # )
        # print(n)
    except ValidationError as ve:
        print(ve)
