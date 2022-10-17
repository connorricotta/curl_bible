from pydantic import BaseModel, Field, validator

COLOR_TEXT_DEFAULT = True
TEXT_ONLY_DEFAULT = False
VERSION_DEFAULT = "ASV"
LENGTH_DEFAULT = 20
WIDTH_DEFAULT = 80
OPTIONS_DEFAULT = ""

# Matches '3','999','1-999','999-1'
VERSE_REGEX = "^(([0-9]{1,3})|([0-9]{1,3}-[0-9]{1,3}))$"
# Matches 'John:3:5','Psalms:119:175'
SINGLE_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:5:John:4:3', 'Numbers:7:1:Psalms:119:175'
MULTI_SEMICOLON_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}:[A-z]*:[0-9]{1,3}:[0-9]{1,3})$"
# Matches 'John:3:1-2','Psalms:119:170-176'
SINGLE_SEMICOLON_DASH_REGEX = "^([A-z]*:[0-9]{1,3}:[0-9]{1,3}-[0-9]{1,3})$"
# Matches 'AAA', 'ZZZ'
VERSION_REGEX = "^([A-Z]{3})$"


class OptionsNames:
    short_to_long = {
        "c": "color_text",
        "l": "length",
        "t": "text_only",
        "w": "width",
        "v": "version",
    }

    options_dict = {
        "color_text": COLOR_TEXT_DEFAULT,
        "length": LENGTH_DEFAULT,
        "text_only": TEXT_ONLY_DEFAULT,
        "width": WIDTH_DEFAULT,
        "version": VERSION_DEFAULT,
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
    options: str | None

    @validator("options")
    def contains_options(cls, opts, values):
        """
        In case the user passes in a list of options, parse them here.
        """
        opt = OptionsNames()
        if opts == "" or opts is None:
            return opts

        # Parse the options string into its constitutent parts
        parsed_option_string = (
            opts.replace("o=", "").replace("options=", "").replace("'", "").split(",")
        )
        option_list = [i.split("=") for i in parsed_option_string]

        # Parse through the options and update the dictionary if the option is there
        for option in option_list:
            option_name = option[0]
            option_value = option[1]
            opt.options_dict[opt.to_long(option_name)] = option_value

        values["color_text"] = is_bool(opt.options_dict["color_text"])
        values["text_only"] = is_bool(opt.options_dict["text_only"])
        # Ensure that 'width' or 'length' are integers and they are greater than 0
        if (type(opt.options_dict["length"]) == int) or (
            str.isnumeric(opt.options_dict["length"])
            and int(opt.options_dict["length"]) > 0
        ):
            values["length"] = int(opt.options_dict["length"])
        if (type(opt.options_dict["width"]) == int) or (
            str.isnumeric(opt.options_dict["width"])
            and int(opt.options_dict["width"]) > 0
        ):
            values["width"] = int(opt.options_dict["width"])
        if len(opt.options_dict["version"]) == 3:
            values["version"] = opt.options_dict["version"].upper()

        return opts

    def update(self, new_options: dict) -> str:
        """
        Manually pull all query values and add them if they are the smaller values.
        """
        params = dict(new_options.query_params)
        options_set = set(("l", "w", "v", "t", "c"))
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
        return ""

    class Config:
        schema_extra = {
            "examples": [
                {
                    "color_text": False,
                    "length": 25,
                }
            ]
        }


def is_bool(bool_test):
    if type(bool_test) == bool:
        return bool_test
    return bool_test.lower() in ("yes", "true", "t", "1")
