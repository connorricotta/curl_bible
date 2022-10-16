from fastapi import FastAPI, Depends
from pydantic import BaseModel, ValidationError, Field, validator
from starlette import requests

app = FastAPI()

COLOR_TEXT_DEFAULT = True
TEXT_ONLY_DEFAULT = False
VERSION_DEFAULT = "ASV"
LENGTH_DEFAULT = 20
WIDTH_DEFAULT = 80
OPTIONS_DEFAULT = ""


class OptionsNames:
    short_to_long = {
        "c": "color_text",
        "l": "length",
        "t": "text_only",
        "w": "width",
        "v": "version",
    }
    # options_dict = {
    #     "color_text": COLOR_TEXT_DEFAULT,
    #     "length": LENGTH_DEFAULT,
    #     "text_only": TEXT_ONLY_DEFAULT,
    #     "width": WIDTH_DEFAULT,
    #     "version": VERSION_DEFAULT,
    # }

    def to_long(self, option):
        """
        Return the full name of the option
        """
        if option in self.short_to_long:
            return self.short_to_long[option]
        else:
            return option

    def is_bool(self, bool_test):
        if type(bool_test) == bool:
            return bool_test
        return bool_test.lower() in ("yes", "true", "t", "1")


class Options(BaseModel):
    def __init__(self, **data):
        """
        Using a ternary (which is required for constructors), check:
            - if both the short and long values are None
                -> Use the Default Value
            - elif the short value is not None
                -> Use the Short Value
            - else
                -> Use the Long Value
        The color_text comparison can be written as:
            if data.get('c') == None and data.get('color_text')==None:
                color_text = True
            elif data.get("c") != None:
                color_text = data.get("c")
            else:
                color_text = data.get("color_text")
        """
        super().__init__(
            # fmt: off
            color_text = \
                COLOR_TEXT_DEFAULT if (data.get('c')==None and data.get('color_text')==None) \
                    else data.get("c") if data.get("c") != None \
                        else data.get("color_text"),
            text_only = \
                TEXT_ONLY_DEFAULT if (data.get('t')==None and data.get('text_only')==None) \
                    else data.get("t") if data.get("t") != None \
                        else data.get("text_only"),
            version = \
                VERSION_DEFAULT if (data.get('v')==None and data.get('version')==None) \
                    else data.get("v") if data.get("v") != None \
                        else data.get("version"),
            length = \
                LENGTH_DEFAULT if (data.get('l')==None and data.get('length')==None) \
                    else data.get("l") if data.get("l") != None \
                        else data.get("length"),
            width = \
                WIDTH_DEFAULT if (data.get('w')==None and data.get('width')==None) \
                    else data.get("w") if data.get("w") != None \
                        else data.get("width"),
            options = \
                OPTIONS_DEFAULT if (data.get('o')==None and data.get('options')==None) \
                    else data.get("o") if data.get("o") != None \
                        else data.get("options"),
            # fmt: on
        )

    def inject(self, new_length):
        self.length = new_length
        return "none"

    color_text: bool | None = Field(default=True)
    text_only: bool | None = Field(default=TEXT_ONLY_DEFAULT)
    version: str | None = Field(default=VERSION_DEFAULT, min_length=3, max_length=3)
    length: int | None = Field(default=LENGTH_DEFAULT, gt=0)
    width: int | None = Field(default=WIDTH_DEFAULT, gt=0)
    options: str | None

    @validator("options")
    def contains_options(cls, opts, values):
        """
        In case the user passes in a list of options, parse them here.
        """
        opt = OptionsNames()
        if opts == "":
            return opts

        # Parse the options string into it's constitutent parts
        parsed_option_string = (
            opts.lstrip("o=").lstrip("options=").replace("'", "").split(",")
        )
        option_list = [i.split("=") for i in parsed_option_string]

        # Parse through the options and update the dictionary if the option is there
        for option in option_list:
            option_name = option[0]
            option_value = option[1]
            opt.options_dict[opt.to_long(option_name)] = option_value

        # The boolean options will accept 'yes','y','0','1', so use a function to convert them.
        values["color_text"] = opt.is_bool(opt.options_dict["color_text"])
        values["text_only"] = opt.is_bool(opt.options_dict["text_only"])
        values["length"] = opt.options_dict["length"]
        values["width"] = opt.options_dict["width"]
        values["version"] = opt.options_dict["version"]

        return opts


@app.get("/")
async def parse_options(request: requests.Request, p: Options = Depends()):
    # async def parse_options(option: Options = Depends()):
    # print(**p)
    p.inject(new_length=42)
    return request.query_params


if __name__ == "__main__":

    try:
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
